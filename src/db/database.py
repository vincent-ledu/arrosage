from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import config.config as local_config

url = local_config.SQLALCHEMY_DATABASE_URL

connect_args = {}
if url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    url,
    pool_pre_ping=True,        # évite les connexions mortes
    pool_recycle=1800,         # recycle au bout de 30 min
    echo=local_config.SQL_ECHO,
    future=True,
    connect_args=connect_args,
)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

if url.startswith("sqlite"):
    from db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

# Helper Flask pour obtenir une session par requête si besoin
def get_session():
    return SessionLocal()
