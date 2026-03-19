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

def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
):

    user_id = request.cookies.get("user_id")

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
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

    new_user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
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

    user = db.query(User).filter_by(email=email).first()

    if not user:

        return {
            "status": "error",
            "message": "Credenciais inválidas"
        }


    if check_password(password, user.password_hash):

        response.set_cookie(
            key="user_id",
            value=str(user.id),
            httponly=True,
            secure=True,
            samesite='lax',
            path="/"
        )

        return {"status": "success"}

    return {
        "status": "error",
        "message": "Credenciais inválidas"
    }


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
            "status": "success",
            "message": "Se o e-mail existir, um link será enviado."
        }

    token = secrets.token_urlsafe(32)

    user.reset_token = token

    user.reset_token_expire = datetime.utcnow() + timedelta(minutes=30)

    db.commit()

    reset_link = f"http://localhost:8000/reset-password?token={token}"

    print("Sending email to:", user.email)
    send_reset_email(user.email, reset_link)
    print("Email sent function executed")

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