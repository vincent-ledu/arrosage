from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import SQLALCHEMY_DATABASE_URL, SQL_ECHO

# SQLite: pragmas utiles, threads
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=SQL_ECHO,
    future=True,
    connect_args=connect_args,
)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Helper Flask pour obtenir une session par requête si besoin
def get_session():
    return SessionLocal()