"""forecast: create table, import data, drop column from tasks

Revision ID: 2a1830e9b62f
Revises: add_min_max_temperature_and_precipitation
Create Date: 2025-08-23 18:48:46.621258

"""
from typing import Sequence, Union

from alembic import op
import requests
import json
import sqlalchemy as sa
import pathlib
from config.config import load_config
from datetime import date , timedelta


# revision identifiers, used by Alembic.
revision: str = 'create_forecast_stats_import_drop_tasks_columns'
down_revision: Union[str, Sequence[str], None] = 'add_min_max_temperature_and_precipitation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

config = load_config()

def upgrade() -> None:
    # 1) Create forecast_stats table
    forecast_stats_table = op.create_table(
        'forecast_stats',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('min_temp', sa.Float, nullable=True),
        sa.Column('max_temp', sa.Float, nullable=True),
        sa.Column('precipitation', sa.Float, nullable=True),
    )

    # 2) Récupération des données open-meteo
    # Latitude/Longitude
    lat = config['coordinates']['latitude']
    lon = config['coordinates']['longitude']
    start_date = "2025-07-11"  # date de début des données historiques
    # date de fin des données historiques (aujourd'hui moins 2 jours, car absent des archives open-meteo)
    end_date = (date.today() - timedelta(days=2)).isoformat()

    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=temperature_2m_min,temperature_2m_max,precipitation_sum"
        f"&timezone=Europe/Paris"
    )
    response = requests.get(url)
    response.raise_for_status()
    meteo_data = response.json()

    d = meteo_data["daily"]

        # Convertir en objets date
    dates = [date.fromisoformat(s) for s in d["time"]]

    rows = [
        {"date": dt, "min_temp": tmin, "max_temp": tmax, "precipitation": pr}
        for dt, tmin, tmax, pr in zip(dates, d["temperature_2m_min"], d["temperature_2m_max"], d["precipitation_sum"])
    ]
    print(f"archive-api - data: {rows}")


    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&forecast_days=1&past_days=1"
        f"&daily=temperature_2m_min,temperature_2m_max,precipitation_sum"
        f"&timezone=Europe/Paris"
    )
    response = requests.get(url)
    response.raise_for_status()
    meteo_data = response.json()

    d = meteo_data["daily"]
    dates = [date.fromisoformat(s) for s in d["time"]]
    for i in range(len(dates)):
        if dates[i] not in [r["date"] for r in rows]:
            rows.append(
                {"date": dates[i], "min_temp": d["temperature_2m_min"][i], "max_temp": d["temperature_2m_max"][i], "precipitation": d["precipitation_sum"][i]}
            )
    
    print(f"forcecast-api - data: {rows}")
    # Insertion en bulk
    op.bulk_insert(forecast_stats_table, rows)

    # 3) Drop min_temp, max_temp, precipitation from tasks
    # SQLite does not support DROP COLUMN directly before v3.35 (2021).
    # Alembic's batch_alter_table uses a workaround (table recreation) for SQLite.
    with op.batch_alter_table('tasks', recreate='always') as batch_op:
        batch_op.drop_column('min_temp')
        batch_op.drop_column('max_temp')
        batch_op.drop_column('precipitation')
    

def downgrade() -> None:

    # 1) Re-add min_temp, max_temp, precipitation to tasks
    with op.batch_alter_table('tasks', recreate='always') as batch_op:
        batch_op.add_column(sa.Column('min_temp', sa.Float, nullable=True))
        batch_op.add_column(sa.Column('max_temp', sa.Float, nullable=True))
        batch_op.add_column(sa.Column('precipitation', sa.Float, nullable=True))

    # 2) impoert data back from forecast_stats to tasks
    op.execute("""
        UPDATE tasks
        SET min_temp = (SELECT fs.min_temp FROM forecast_stats fs WHERE fs.date = date(tasks.created_at) LIMIT 1),
            max_temp = (SELECT fs.max_temp FROM forecast_stats fs WHERE fs.date = date(tasks.created_at) LIMIT 1),
            precipitation = (SELECT fs.precipitation FROM forecast_stats fs WHERE fs.date = date(tasks.created_at) LIMIT 1)
        WHERE EXISTS (SELECT 1 FROM forecast_stats fs WHERE fs.date = date(tasks.created_at))
    """)
    # 3) Drop forecast_stats table
    op.drop_table('forecast_stats')