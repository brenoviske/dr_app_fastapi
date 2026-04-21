from fastapi import APIRouter , Form , Depends  , HTTPException
from src.database.connection import get_db
from src.patients.model import Patient
from src.users.model import User
from src.patients.controller import PatientController
from sqlalchemy.orm import Session
from src.users.router import get_current_user

router = APIRouter()

# -------- Making the class patient models right here ---


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
        name:str = Form(...),
        age:int = Form(...),
        cpf:str = Form(...),
        phone:str = Form(...),
        status:str = Form(None),
        amount:float = Form(None),
        appointment:str = Form(None),
        modality:str = Form(None),
        note:str = Form(None),
        user:User = Depends(get_current_user),
        db:Session = Depends(get_db),
):

    if modality:
        modality = modality.lower()

    if len(cpf) < 11 or len(cpf) > 11:

        return {'status':'error','message':'CPF neccesita ter 11 digitos'}

    # Checking to see if the cpf only contain numbers

    for i in cpf:
        if i.isalpha():

            return {'status':'error','message':'CPF não pode incluir letras'}

    existing_cpf = db.query(Patient).filter_by(
        cpf = cpf,
        user_id = user.id,
    ).first()

    if existing_cpf:
        return {'status':'error','message':'CPF já cadastrado'}

    new_patient = Patient(
        name = name,
        age = age,
        cpf = cpf,
        phone= phone,
        status = status.lower(),
        amount = amount,
        appointment= appointment,
        modality = modality,
        note = note,
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
        name:str = Form(...),
        age:int = Form(...),
        cpf:str = Form(...),
        phone:str = Form(...),
        status:str = Form(None),
        amount:float = Form(None),
        appointment:str = Form(None),
        modality:str = Form(None),
        note:str = Form(None),
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):

    patient = get_current_patient(patient_id, db)
    return PatientController.update(patient.id, user.id,
                                    name, age,cpf, phone,status,amount,appointment,modality,
                                    note,db)

