"""
SQLAlchemy engine and session helpers.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from infrastructure.config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_engine():
    return engine


def get_session() -> Session:
    return SessionLocal()
