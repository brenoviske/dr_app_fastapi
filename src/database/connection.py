import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base , sessionmaker
from dotenv import load_dotenv

load_dotenv() # Gathering environment variables

Base = declarative_base()

url = os.getenv('DATABASE_URL')

engine = create_engine(url)
Session = sessionmaker(bind=engine)

def get_db():

    db = Session()

    try:
        yield db

    except Exception as e :
        print('Error:',e)
        raise e
    finally: db.close()

