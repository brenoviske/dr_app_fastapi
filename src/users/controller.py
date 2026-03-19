from src.users.repo import UserRepo
from src.users.model import User
from sqlalchemy.orm import Session


class UserController:

    @staticmethod
    def add(new_user:User,db:Session):
        return UserRepo.add_user(new_user,db)

    @staticmethod
    def delete(id:int, db:Session):
        return UserRepo.remove_user(id,db)

    @staticmethod
    def update(id:int,email:str,username:str,db:Session):
        return UserRepo.update_user(id,email,username,db)

