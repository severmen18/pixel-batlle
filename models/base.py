from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


Base = declarative_base()
metadata = Base.metadata

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/pixel_battle"



engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal  = sessionmaker(autocommit=False, autoflush=False, bind=engine)
