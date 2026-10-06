"""
SQLAlchemy engine + session factory. Every request that touches the
database calls get_db() as a FastAPI dependency, which hands out one
session per request and always closes it afterward, even on error.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

# pool_pre_ping: a Postgres restart or idle-connection drop would otherwise
# surface as one failed request / task per stale pooled connection.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
