from src.users.model import User
from sqlalchemy.orm import Session

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

            return {'status':'success'}

        except Exception as e:

            return {'status':'error','message':e}

    @staticmethod
    def remove_user(id:int, db:Session):

        existing_user = UserRepo.find_by_Id(id,db)

        if not existing_user:

            return {'status':'error','message':'Usuário nao existente'}

        try:

            db.delete(existing_user)
            db.commit()

            return {'status':'success'}

        except Exception as e:

            db.rollback()

            return {'status':'error','message':str(e)}

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



