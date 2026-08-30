"""
SQLAlchemy engine + session factory. Every request that touches the
database calls get_db() as a FastAPI dependency, which hands out one
session per request and always closes it afterward, even on error.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
