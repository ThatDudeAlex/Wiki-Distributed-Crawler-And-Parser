import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from database.db_models.models import Base

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, bind=engine)


def init_db():
    """
    Initializes the database schema by creating all defined tables

    This should only be run during setup or migration workflows
    """
    Base.metadata.create_all(bind=engine)
