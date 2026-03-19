from src.database.connection import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime , Enum
from datetime import datetime

class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True,autoincrement=True,nullable=False)
    email = Column(String(200),nullable=False,unique=True)
    username =  Column(String(200), nullable = False , unique=True)
    password_hash = Column(String(512), nullable=False)
    reset_token = Column(String(200), nullable = True , index=True)
    reset_token_expire = Column(DateTime,nullable = True)
    created_at = Column(DateTime,nullable=False,default=datetime.utcnow)

    patients = relationship("Patient",back_populates="user"
                            , cascade='all,delete')

    def to_json(self):

        return {
            "id":self.id,
            "email":self.email,
            "username":self.username,
            "created_at":self.created_at,
        }


