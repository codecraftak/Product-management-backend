from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db_url="mysql+pymysql://root:password@localhost:3306/first_sql_fastapi"

engine=create_engine(db_url, echo=True)
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base= declarative_base() 