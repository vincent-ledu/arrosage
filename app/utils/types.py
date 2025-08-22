# types.py
from datetime import datetime, timezone
from sqlalchemy.types import TypeDecorator, DateTime

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class UTCDateTime(TypeDecorator):
    """
    Stocke un datetime en UTC (naïf) et renvoie un datetime aware (UTC) à la lecture.
    - Compatible SQLite (qui n’a pas de timezone native)
    - Portable vers Postgres/MySQL
    """
    impl = DateTime(timezone=False)   # on stocke naïf = UTC
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("UTCDateTime attend un datetime 'aware'.")
        # Convertit en UTC et enlève tzinfo pour stockage
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Ré-attache UTC à la lecture
        return value.replace(tzinfo=timezone.utc)
