import stripe
import numpy as np
import os
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from sklearn.linear_model import LinearRegression
from dotenv import load_dotenv
import uvicorn

# Importações das suas dependências e modelos
from src.users.router import get_current_user, redirect_if_authenticated
from src.users.model import User
from src.patients.model import Patient
from src.database.connection import get_db , Base , engine
from src.users.router import router as user_router
from src.patients.router import router as patient_router
load_dotenv()

stripe_key = os.getenv('stripe_key')
stripe.api_key = stripe_key

Base.metadata.create_all(bind = engine) # Generating all the tables on the database
app = FastAPI()
templates = Jinja2Templates(directory='src/frontend/templates')
app.mount("/static", StaticFiles(directory='src/frontend/static'), name="static")
app.include_router(user_router,prefix='/users',tags=['users'])
app.include_router(patient_router,prefix='/patients', tags=['patients'])


# ---------- FUNÇÕES UTILITÁRIAS ---------- #

def render(template: str, request: Request, **kwargs):
    """Sua função original para simplificar o retorno de templates."""
    context = {"request": request}
    context.update(kwargs)
    return templates.TemplateResponse(template, context)


def mean(nums: list[float]) -> float:
    return sum(nums) / len(nums) if nums else 0.0


# ---------- EXCEPTION HANDLERS (BLOQUEIO GLOBAL) ---------- #

@app.exception_handler(401)
async def auth_exception_handler(request: Request, exc: HTTPException):
    # Se não estiver logado, manda para a Home/Login
    return RedirectResponse(url="/", status_code=303)


@app.exception_handler(403)
async def trial_expired_handler(request: Request, exc: HTTPException):
    # Se o trial expirou, manda para o Billing
    return RedirectResponse(url="/billing", status_code=303)


# ---------- ROTAS PÚBLICAS ---------- #

@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):

    if redirect_if_authenticated(request,db):

        return RedirectResponse(url='/main',status_code=303)
    return render('index.html', request)


@app.get('/signup')
def signup(request: Request):
    return render('signup.html', request)


@app.get('/billing')
def pricing_page(request: Request):
    return render('billing.html', request)


# ---------- ROTAS PROTEGIDAS ---------- #

@app.get('/main')
def main(request: Request, user: User = Depends(get_current_user) , db:Session = Depends(get_db)):
    plan = 'Pro' if user.subscription_status == 'active' else 'Gratuito'

    return render('main.html', request, user=user, plan=plan)


@app.get('/patients/all')
def get_patients(current_user:User = Depends(get_current_user), db:Session = Depends(get_db)):

    patients = db.query(Patient).filter_by(user_id = current_user.id).all()

    return [ p.to_json() for p in patients ]
@app.get('/dashboard')
def dashboard(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    # Fetching here the user to upload the current plan there

    plan = 'Pro' if current_user.subscription_status == 'active' else 'Gratuito'
    patients = db.query(Patient).filter_by(user_id=current_user.id).all()

    # Métricas Financeiras
    amounts = [p.amount for p in patients if p.amount is not None]
    total_amount = round(sum(amounts), 2) if amounts else 0
    min_revenue = round(min(amounts),2)
    max_revenue = round(max(amounts),2)
    mean_rev = round(mean(amounts), 2)

    # Contagens via SQL (Garante 0 em vez de None)
    stats = db.query(
        func.coalesce(func.sum(case((Patient.status == 'confirmado', 1), else_=0)), 0).label('conf'),
        func.coalesce(func.sum(case((Patient.status == 'pendente', 1), else_=0)), 0).label('pend'),
        func.coalesce(func.sum(case((Patient.status == 'cancelado', 1), else_=0)), 0).label('canc'),
        func.coalesce(func.sum(case((Patient.modality.in_(['cirurgia', 'Cirurgia']), 1), else_=0)), 0).label('surg'),
        func.coalesce(func.sum(case((Patient.modality.in_(['consulta', 'Consulta']), 1), else_=0)), 0).label('cons')
    ).filter_by(user_id=current_user.id).first()

    # Ordenação por idade
    patients_sorted = sorted(patients, key=lambda p: p.age)
    oldest = patients_sorted[-1] if patients_sorted else None
    youngest = patients_sorted[0] if patients_sorted else None

    return render('dashboard.html', request,
                  number_patients=len(patients),
                  total_amount=total_amount,
                  mean_revenue=mean_rev,
                  confirmed_patients=stats.conf,
                  pending_patients=stats.pend,
                  cancelled_patients=stats.canc,
                  surgeries_count=stats.surg,
                  consults_count=stats.cons,
                  oldest_patient=oldest,
                  youngest_patient=youngest,
                  plan = plan,
                  min_revenue = min_revenue,
                  max_revenue = max_revenue

                  )


@app.get('/profile')
def profile_page(
        request:Request,
        current_user:User = Depends(get_current_user),
        db:Session = Depends(get_db)
):

    user = db.query(User).filter_by(
        id = current_user.id
    ).first()

    if user:

        return templates.TemplateResponse(
           'profile.html' ,
            {'request':request,'user':user}
        )

    return render('profile.html',request)


@app.get('/finance')
def finance_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    # Fetching here again the users plan

    plan = 'Pro' if user.subscription_status == 'active' else 'Gratuito'
    patients = db.query(Patient).filter(Patient.user_id == user.id, Patient.status == 'Confirmado').all()

    monthly_totals = defaultdict(float)
    for p in patients:
        if p.created_at:
            month_key = p.created_at.strftime('%Y-%m')
            monthly_totals[month_key] += float(p.amount or 0.0)

    if not monthly_totals:
        labels, values = [datetime.now().strftime('%Y-%m')], [0.0]
    else:
        labels = sorted(monthly_totals.keys())[-11:]
        values = [float(monthly_totals[k]) for k in labels]

    # Predição IA
    prediction = values[-1] if len(values) == 1 else 0.0
    if len(values) > 1:
        model = LinearRegression().fit(np.array(range(len(values))).reshape(-1, 1), np.array(values))
        prediction = max(0, float(model.predict([[len(values)]])[0]))

    return render("finance.html", request, user=user, stats={
        "labels": labels,
        "revenue_list": values,
        "mean_revenue": mean(values),
        "prediction": round(prediction, 2),
        "total_revenue": round(sum(values), 2),
        'plan':plan
    })


# ---------- PAGAMENTOS ---------- #

@app.post("/create-checkout-session")
def create_checkout_session(user: User = Depends(get_current_user)):
    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer_email=user.email,
        line_items=[{"price": os.getenv('price_stripe_id'), "quantity": 1}],
        success_url="https://drappfastapi-production.up.railway.app/main?payment=success",
        cancel_url="https://drappfastapi-production.up.railway.app/billing",
        metadata={"user_id": user.id}
    )
    return {"checkout_url": session.url}


@app.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return {"error": str(e)}

    # This is the moment Stripe tells us the Customer ID and Subscription ID
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # 1. Look up the user using the metadata we sent in create_checkout_session
        user_id = session.get("metadata", {}).get("user_id")

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # 2. SAVE THE IDs! This is what was missing.
                user.stripe_customer_id = session.get("customer")
                user.stripe_subscription_id = session.get("subscription")
                user.subscription_status = "active"
                db.commit()
                print(f"User {user.email} updated with Customer ID: {user.stripe_customer_id}")

    # Handle Cancellation (User went to Stripe and cancelled)
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_status = "expired"
            db.commit()

    return {"status": "success"}


if __name__ == '__main__':
    uvicorn.run(app)