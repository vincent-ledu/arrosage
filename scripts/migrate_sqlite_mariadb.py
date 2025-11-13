# migrate_sqlite_to_mariadb.py
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date, datetime
import os
from db.models import Base, Task
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # charge les variables d'environnement depuis le fichier .env

SQLITE_URL = "sqlite:///./arrosage.db"  # adapte le chemin
MARIADB_URL = os.environ.get("DATABASE_URL")
if not MARIADB_URL:
    logger.error("DATABASE_URL is not set in environment variables.")
    exit(1)

src_engine = create_engine(SQLITE_URL, future=True)
dst_engine = create_engine(MARIADB_URL, pool_pre_ping=True, future=True)

# crée les tables côté MariaDB
Base.metadata.create_all(dst_engine)


def to_date(v):
    """ Convertit une valeur en date (sans heure) """
    if v is None:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, str):
        return date.fromisoformat(v[:10])
    if isinstance(v, datetime):
        return v.date()
    raise ValueError(f"Impossible de convertir en date: {v!r}")


def to_datetime_naive_utc(v):
    """ Convertit une valeur en datetime UTC naive (sans info de fuseau) """
    if v is None:
        return None
    if isinstance(v, datetime):
        # si aware => transforme en UTC puis drop tz
        if v.tzinfo is not None:
            v = v.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return v
    if isinstance(v, str):
        # best effort: "YYYY-MM-DD HH:MM:SS"
        return datetime.fromisoformat(v.replace("Z", "")).replace(tzinfo=None)
    raise ValueError(f"Impossible de convertir en datetime: {v!r}")


with Session(src_engine) as s_src, Session(dst_engine) as s_dst:
    # Tasks
    for (t,) in s_src.execute(select(Task)).all():
        s_dst.merge(
            Task(
                id=t.id,
                duration=t.duration,
                status=t.status,
                created_at=to_datetime_naive_utc(t.created_at),
                updated_at=to_datetime_naive_utc(t.updated_at),
            )
        )
    s_dst.commit()
