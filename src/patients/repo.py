from src.patients.model import Patient
from sqlalchemy.orm import Session


class PatientRepo:

    @staticmethod
    def add(patient:Patient,db:Session):

        existing_name = db.query(Patient).filter_by(
            name = patient.name,
            user_id = patient.user_id
        ).first()

        if existing_name:

            return {'status':'error','message':'Nome do paciente já se encontra no banco de dados'}


        try:

            db.add(patient)
            db.commit()
            db.refresh(patient)

            return {'status':'success', 'patient':patient}

        except Exception as e:

            db.rollback()

            print('Error',e)

            return {'status':'error','message':e}


    @staticmethod
    def delete(id:int,user_id:int,db:Session):

        patient = db.query(Patient).filter_by(
            id = id,
            user_id = user_id
        ).first()

        if not patient:
            return {'status':'error','message':'Paciente não encontrado'}

        try:

            db.delete(patient)
            db.commit()

            return {'status':'success'}

        except Exception as e:

            db.rollback()

            return {'status':'error','message':e}

    @staticmethod
    def update(id:int,user_id:int,name:str,age:int,cpf:str,phone:str,status:str,amount:float,appointment:str,modality:str,note:str,db:Session):

        patient = db.query(Patient).filter_by(
            id = id,
            user_id = user_id
        ).first()

        if not patient:
            return {'status':'error','message':'Paciente não encontrado'}

        try:

            if name:
                patient.name = name
            if age:
                patient.age = age
            if cpf:
                patient.cpf = cpf
            if phone:
                patient.phone = phone
            if status:
                patient.status = status
            if note:
                patient.note = note
            if amount:
                patient.amount = amount
            if appointment:
                patient.appointment = appointment
            if modality:
                patient.modality = modality


            db.commit()

            return {'status':'success'}

        except Exception as e:

            db.rollback()

            return {'status':'error','message':e}


    @staticmethod
    def get_all(user_id:int,db:Session):
        patients = db.query(Patient).filter_by(
            user_id = user_id
        ).all()

        return patients


