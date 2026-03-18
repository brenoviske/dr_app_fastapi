from fastapi import FastAPI , Request , Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from users.model import User
from database.connection import get_db , Base , engine
from patients.model import Patient
from sqlalchemy.orm import Session
from sqlalchemy import func , case
import uvicorn
from users.router import router as user_router, get_current_user
from patients.router import router as patient_router
from dotenv import load_dotenv
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# This finds the directory where main.py lives (src/)
# .parent.parent moves up to the root (dr_fast_api/)

# 1. Get the directory where main.py is located (e.g., /app/src)
current_file = Path(__file__).resolve()

# 2. Go up one level to reach the project root (e.g., /app)
project_root = current_file.parent.parent

# 3. Construct the absolute path to the static folder
static_dir = project_root / "frontend" / "static"

# 4. Mount the directory
load_dotenv() # Loading all the environment variables right here

Base.metadata.create_all(bind=engine)
app = FastAPI()
templates = Jinja2Templates(directory="./frontend/templates")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(patient_router, prefix="/patients", tags=["patients"])

def render(template:str,request:Request):
    return templates.TemplateResponse(template,{"request":request})

def mean(nums:list[float]) -> float:
    return sum(nums)/ len(nums) if nums else None

@app.get("/")
def index(
    request:Request,

):return render('index.html',request)

@app.get('/signup')
def signup(
        request:Request,
): return render('signup.html',request)

@app.get('/main')
def main(
        request:Request,
        current_user:User = Depends(get_current_user),
        db:Session = Depends(get_db)
):

    user = db.query(User).filter_by(id=current_user.id).first()

    return templates.TemplateResponse(
        'main.html',
        {'request': request, 'user': user}
    )

@app.get('/profile')
def profile(
        request:Request,
        current_user:User = Depends(get_current_user),
        db:Session = Depends(get_db)
):
    user = db.query(User).filter_by(
        id = current_user.id
    ).first()

    return templates.TemplateResponse(
        'profile.html',
        {'request':request, 'user': user}
    )

@app.get('/recover')
def recover_password(
        request:Request
):
    return render('forgetpass.html', request)

@app.get("/patients/all")
def get_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    patients = db.query(Patient).filter_by(
        user_id=current_user.id
    ).all()

    return [ p.to_json() for p in patients]

@app.get('/forgotpassword')
def forgot_password(
        request:Request,
):
    return render('forgotpassword.html',request)

@app.get('/reset-password')
def reset_password(
        request:Request,
        token:str
):
    return templates.TemplateResponse(
        'redefine_password.html',
        {'request': request, 'token': token}
    )

@app.get('/dashboard')
def dashboard(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):

    # Calculating the total amount of patients
    patients = db.query(Patient).filter_by(user_id=current_user.id).all()

    number_patients = len(patients)

    amount = [ p.amount for p in patients if p.amount is not None
               ]

    if amount:

        total_amount = round(sum(amount),2)
        max_revenue = round(max(amount),2)
        min_revenue = round(min(amount),2)
        mean_revenue = round(mean(amount),2)

    else:
        total_amount = 0
        max_revenue = 0
        min_revenue = 0
        mean_revenue = 0


    # Count confirmed, pending, and canceled patients
    status_counts = db.query(
        func.sum(case(
            (Patient.status == 'confirmado', 1),
            else_=0)).label('confirmed_count'),
        func.sum(case(
        (Patient.status == 'pendente', 1),
            else_=0)).label('pending_count'),
        func.sum(case(
            (Patient.status == 'cancelado', 1),
            else_=0)).label('cancelled_count')
    ).filter_by(user_id=current_user.id).first()



    # Referencing per status

    confirmed_patients = status_counts.confirmed_count if status_counts else 0
    pending_patients = status_counts.pending_count if status_counts else 0
    cancelled_patients = status_counts.cancelled_count if status_counts else 0

    # Count surgeries and consults
    modality_counts = db.query(
        func.sum(case(
            (Patient.modality.in_(['cirurgia', 'Cirurgia']), 1),
            else_=0)).label('surgeries_count'),
        func.sum(case(
            (Patient.modality.in_(['consulta', 'Consulta']), 1),
            else_=0)).label('consults_count')
    ).filter_by(user_id=current_user.id).first()

    surgeries_count = modality_counts.surgeries_count if modality_counts and modality_counts.surgeries_count else 0
    consults_count = modality_counts.consults_count if modality_counts and modality_counts.consults_count else 0

    # Gathering information per age


    # Sorting the list per age

    patients = sorted(patients,key=lambda p:p.age)

    if patients:
        oldest_patient = patients[-1]
        youngest_patient = patients[0]
    else:
        oldest_patient = None
        youngest_patient = None

    return templates.TemplateResponse(
        'dashboard.html',
        {
            'request': request,
            'number_patients': number_patients,
            'total_amount': total_amount,
            'max_revenue': max_revenue,
            'min_revenue': min_revenue,
            'mean_revenue': mean_revenue,
            'confirmed_patients': confirmed_patients,
            'pending_patients': pending_patients,
            'cancelled_patients': cancelled_patients,
            'surgeries_count': surgeries_count,
            'consults_count': consults_count,
            'oldest_patient':oldest_patient,
            'youngest_patient':youngest_patient,
        }
    )


if __name__ == '__main__':

    uvicorn.run(app)