from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import config.config as local_config

# SQLite: pragmas utiles, threads
connect_args = {}
engine = create_engine(
    local_config.SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,        # évite les connexions mortes
    pool_recycle=1800,         # recycle au bout de 30 min
    echo=local_config.SQL_ECHO,
    future=True,
    connect_args=connect_args,
)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Helper Flask pour obtenir une session par requête si besoin
def get_session():
    return SessionLocal()