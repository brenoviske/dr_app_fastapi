from fastapi import APIRouter, Depends, Form, Response, HTTPException, Request
from src.users.model import User
from src.users.controller import UserController
from src.database.connection import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import bcrypt
import secrets
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()

email_address = os.getenv("EMAIL_ADDRESS")
email_password = os.getenv("EMAIL_PASSWORD")

# ---------- EMAIL CONFIGURATION ---------- #

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_ADDRESS = email_address
EMAIL_PASSWORD = email_password




def send_reset_email(user_email: str, reset_link: str):

    try:
        message = EmailMessage()

        message["Subject"] = "Redefinição de Senha – DoctorFlow"
        message["From"] = EMAIL_ADDRESS
        message["To"] = user_email

        message.set_content(f"""
Olá,

Equipe DoctorFlow, caro usuário.
Recebemos uma solicitação para redefinir a senha da sua conta.

Acesse o link abaixo para redefinir sua senha , você será redirecionado ao login caso consiga alterar sua senha:

{reset_link} 

Não compartilhe ou divulgue este link com terceiros por medidas de privacidade dos seus dados
""")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:

            smtp.starttls()

            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

            smtp.send_message(message)

        print("Email successfully sent")

    except Exception as e:

        print("EMAIL ERROR:", e)

# ---------- SECURITY METHODS ---------- #

def hash_password(plain: str):

    hashed = bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def check_password(plain: str, hashed: str):

    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8")
    )


# ---------- AUTH ---------- #

def trial_expired(
        user:User,
        db:Session = Depends(get_db)
):

    if user.subscription_status == "active":
        return False

    if user.subscription_status == 'expired':

        return True

    if datetime.utcnow() > user.trial_end:
        user.subscription_status = 'expired'
        db.commit() # Commiting subscription status to the database
        return True

    return False

def redirect_if_authenticated(request:Request, db:Session = Depends(get_db)):

    user_id = request.cookies.get('user_id')

    if user_id:

        user = db.query(User).filter_by(
            id = int(user_id)
        ).first()

        if user:

            if not trial_expired(user,db):
                return True

    return False


def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
):

    token = request.cookies.get('access_token')
    print(f"DEBUG: Token recebido no checkout return: {token}")
    user_id = request.cookies.get("user_id")

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Não autenticado"
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )

    if trial_expired(user,db):
        raise HTTPException(
            status_code=403,
            detail='Plano gratuito expirado'
        )

    return user


router = APIRouter()


# ---------- REGISTER ---------- #

@router.post("/add")
async def add(
        email: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    trial_end = datetime.utcnow() + timedelta(days=7)
  # Initiating trial end timer to affect or restrict the users behavior if they are not paying it
    new_user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        trial_end = trial_end
    )


    return UserController.add(new_user, db)


# ---------- LOGIN ---------- #

@router.post("/login")
async def login(
        response: Response,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    # 1. Primeiro: O usuário existe?
    user = db.query(User).filter_by(email=email).first()

    if not user or not check_password(password, user.password_hash):
        return {
            "status": "error",
            "message": "Credenciais inválidas"
        }

    # 2. Segundo: Verificação de assinatura (opcional bloquear aqui ou na /main)
    if user.subscription_status == 'expired':
        return {
            'status': 'expired',
            'redirect': '/billing'
        }

    # 3. Configuração do Cookie (Ajustada para Localhost e Stripe)
    response.set_cookie(
        key="user_id",  # Certifique-se que get_current_user busca por 'user_id'
        value=str(user.id),
        httponly=True,
        # MUITO IMPORTANTE:
        secure=False,  # Mude para True apenas no Railway (HTTPS)
        samesite='lax',  # Permite que o cookie volte do Stripe para o seu site
        path="/"
    )

    return {"status": "success"}


# ---------- DELETE ACCOUNT ---------- #

@router.delete("/delete")
async def delete(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):

    return UserController.delete(current_user.id, db)


# ---------- UPDATE USER ---------- #

@router.put("/update")
async def update(
        email: str = Form(None),
        username: str = Form(None),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):

    return UserController.update(
        current_user.id,
        email,
        username,
        db
    )


# ---------- FORGOT PASSWORD ---------- #

@router.post("/forgot-password")
async def forgot_password(
        email: str = Form(...),
        db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == email
    ).first()

    # security: do not reveal if email exists
    if not user:

        return {
            "status": "error",
            "message": "Se o e-mail existir, um link será enviado."
        }

    token = secrets.token_urlsafe(32)

    user.reset_token = token

    user.reset_token_expire = datetime.utcnow() + timedelta(minutes=30)

    db.commit()

    reset_link = f"https://drappfastapi-production.up.railway.app/reset-password?token={token}"

    send_reset_email(user.email, reset_link)

    return {
        "status": "success",
    }


# ---------- RESET PASSWORD ---------- #

@router.post("/redefine")
def redefine_password(
        token:str  = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    print("TOKEN RECEIVED:", token)
    print("PASSWORD RECEIVED:", password)

    user = db.query(User).filter(
        User.reset_token == token
    ).first()

    if not user:

        return {
            "status": "error",
            "message": "Token inválido"
        }

    if not user.reset_token_expire or datetime.utcnow() > user.reset_token_expire:
        user.reset_token = None
        user.reset_token_expiry = None

        db.commit()

        return {
            "status": "error",
            "message": "Token expirado"
        }

    if check_password(password, user.password_hash):

        return {
            "status": "error",
            "message": "A nova senha deve ser diferente da anterior"
        }

    user.password_hash = hash_password(password)

    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return {
        "status": "success"
    }

