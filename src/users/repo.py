from src.users.model import User
from sqlalchemy.orm import Session
import stripe
from dotenv import load_dotenv
import os
from email.message import EmailMessage
import smtplib

load_dotenv()

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def greetings_email(user_email: str, username: str):
    try:

        message = EmailMessage()

        message['Subject'] = 'Boas Vindas ao DoctorFLow!'
        message['From'] = EMAIL_ADDRESS
        message['To'] = user_email

        message.set_content(f"""

    Olá caro usuário {username}.
    Ficamos honrados em saber de que você agora faz parte do time DoctorFlow.

    Gerencie , adicione e edite seus pacientes , tendo acesso a visões gerais e financeiras , 
    acompanhadas de dashboards interativos para sua própria experiência.

    Sua versão grátis se inicia agora e termina após um período de 7 dias.
    Aproveite para olhar nosso planos e continuar a usar todos os recursos.

    Agredecemos mais uma vez por se juntar ao time DoctorFlow.


    """)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:

            smtp.starttls()

            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

            smtp.send_message(message)

            print('Email successfully sent')

    except Exception as e:

        print('Error:', e)

class UserRepo:

    @staticmethod
    def find_by_Id(id:int,db:Session):
        return db.query(User).filter_by(id = id).first()

    @staticmethod
    def add_user(user:User, db:Session):

        user_email = db.query(User).filter_by(
            email = user.email,
        ).first()

        username = db.query(User).filter_by(
            username = user.username).first()

        if user_email:

            return {'status':'error','message':'Email já em uso'}

        if username:

            return {'status':'error','message':'Nome de usuário já em uso'}

        try:

            db.add(user)
            db.commit()
            db.refresh(user)

            greetings_email(user.email, user.username)

            return {'status':'success'}

        except Exception as e:

            return {'status':'error','message':e}

    @staticmethod
    def remove_user(id: int, db: Session):
        existing_user = UserRepo.find_by_Id(id, db)

        if not existing_user:
            return {'status': 'error', 'message': 'Usuário não existente'}

        try:
            # 1. STOP THE BLEEDING (Stripe Cancellation)
            # Check if the user ever started a Stripe journey
            if existing_user.stripe_customer_id:
                try:
                    # This cancels all subscriptions and deletes the customer profile
                    stripe.Customer.delete(existing_user.stripe_customer_id)
                except stripe.error.StripeError as e:
                    # We log this, but we don't necessarily want to block
                    # the DB deletion if the Stripe account is already gone.
                    print(f"Stripe cleanup failed: {e}")

            # 2. DATABASE CLEANUP
            # Your 'cascade=all,delete' on the 'patients' relationship
            # will automatically handle the patient records.
            db.delete(existing_user)
            db.commit()

            return {'status': 'success'}

        except Exception as e:
            db.rollback()
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def update_user(id:int , email:str , username:str, db:Session):

        existing_user = UserRepo.find_by_Id(id,db)

        if not existing_user:

            return {'status':'error','message':'Usuário nao encontrado'}

        if email and email != existing_user.email:
            check_email = db.query(User).filter_by(email=email).first()
            if check_email:
                return {'status':'error','message':'Email já em uso'}

        if username and username != existing_user.username:
            check_username = db.query(User).filter_by(username=username).first()
            if check_username:
                return {'status':'error','message':'Nome de usuário já em uso'}

        try:

            if email:

                existing_user.email = email

            if username:

                existing_user.username = username

            db.commit()

            return {'status':'success'}

        except Exception as e:

            db.rollback()

            return {'status':'error','message':str(e)}



