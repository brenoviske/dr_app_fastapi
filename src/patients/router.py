from fastapi import APIRouter , Form , Depends  , HTTPException
from src.database.connection import get_db
from src.patients.model import Patient
from pydantic import BaseModel
from src.users.model import User
from src.patients.controller import PatientController
from sqlalchemy.orm import Session
from src.users.router import get_current_user

router = APIRouter()

# -------- Making the class patient models right here ---

class PatientCreate(BaseModel):

    name:str
    age:int
    cpf:str
    phone:str
    status:str
    amount:float
    appointment:str
    modality:str
    note:str


class PatientUpdate(BaseModel):

    name:str
    age:int
    cpf:str
    phone:str
    status:str
    amount:float
    appointment:str
    modality:str
    note:str




def get_current_patient(
        patient_id: int ,
        db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter_by(
        id = patient_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Paciente não encontrado"
        )

    return patient

@router.post('/add')
def add(
        pt_create:PatientCreate,
        user:User = Depends(get_current_user),
        db:Session = Depends(get_db),
):

    if pt_create.modality:
        pt_create.modality = pt_create.modality.lower()

    if len(pt_create.cpf) < 11 or len(pt_create.cpf) > 11:

        return {'status':'error','message':'CPF neccesita ter 11 digitos'}

    # Checking to see if the cpf only contain numbers

    for i in pt_create.cpf:
        if i.isalpha():

            return {'status':'error','message':'CPF não pode incluir letras'}

    existing_cpf = db.query(Patient).filter_by(
        cpf = cpf,
        user_id = user.id,
    ).first()

    if existing_cpf:
        return {'status':'error','message':'CPF já cadastrado'}

    new_patient = Patient(
        name = pt_create.name,
        age = pt_create.age,
        cpf = pt_create.cpf,
        phone= pt_create.phone,
        status = pt_create.status.lower(),
        amount = pt_create.amount,
        appointment= pt_create.appointment,
        modality = pt_create.modality,
        note = pt_create.note,
        user_id= user.id
    )

    return PatientController.add(new_patient,db)


@router.delete('/delete')
def delete(
        current_patient:Patient = Depends(get_current_patient),
        current_user:User = Depends(get_current_user),
        db:Session = Depends(get_db),
):
    return PatientController.delete(current_patient.id, current_user.id , db)


@router.put('/update')
def update(
        patient_id:int,
        new_update:PatientUpdate,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):

    patient = get_current_patient(patient_id, db)
    return PatientController.update(patient.id, user.id,
                                    new_update.name, new_update.age, new_update.cpf, new_update.phone, new_update.status,new_update.amount,new_update.appointment,new_update.modality,
                                    new_update.note,db)

