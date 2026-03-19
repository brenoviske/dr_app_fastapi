from src.patients.model import Patient
from src.patients.repo import PatientRepo
from sqlalchemy.orm import Session

class PatientController:

    @staticmethod
    def add(patient: Patient, db:Session):

        return PatientRepo.add(patient, db)

    @staticmethod
    def delete(id:int,user_id:int,db:Session):

        return PatientRepo.delete(id, user_id,db)

    @staticmethod
    def update(id:int,user_id:int,name:str,
    age:int,cpf:str,phone:str,status:str,amount:float,appointment:str,modality:str,note:str,db:Session):

        return PatientRepo.update(id, user_id,name, age, cpf, phone,status,amount,appointment,modality, note,db)

