from database.connection import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float, null
from datetime import datetime
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

def decrypt_cpf(cpf_encrypted: str):
    return cipher.decrypt(cpf_encrypted.encode()).decode()

def decrypt_phone(phone_encrypted:str):
    return cipher.decrypt(phone_encrypted.encode()).decode()

class Patient(Base):

    __tablename__ = 'patients'

    id = Column(Integer, primary_key = True, autoincrement = True , nullable=False)
    name = Column(String(200), nullable = False)
    age = Column(Integer, nullable = False)
    cpf= Column(String(11) , nullable = False, unique = True)
    phone = Column(String(11), nullable = False)
    amount = Column(Float, nullable = True)
    status = Column(String(200), nullable = True )
    appointment = Column(String(200) , nullable = True)
    modality = Column(String(200), nullable = True)
    note = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable = False)

    user_id = Column(Integer, ForeignKey('users.id'), nullable = False)
    user = relationship("User", back_populates="patients")

    def to_json(self):

        return {
            'id' : self.id,
            'name' : self.name,
            'age' : self.age,
            'cpf' : self.cpf,
            'phone' : self.phone,
            'amount': self.amount,
            'status':self.status,
            'appointment' : self.appointment,
            'modality' : self.modality,
            'note' : self.note,

        }