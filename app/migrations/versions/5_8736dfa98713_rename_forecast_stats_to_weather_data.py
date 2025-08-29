"""Rename forecast_stats to weather_data.

Revision ID: 8736dfa98713
Revises: e13ea07745b5
Create Date: 2025-08-26 17:18:18.163194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '8736dfa98713'
down_revision: Union[str, Sequence[str], None] = 'e13ea07745b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_TABLE = "forecast_stats"
NEW_TABLE = "weather_data"
OLD_IX_PREFIX = "ix_forecast_stats_"
NEW_IX_PREFIX = "ix_weather_data_"


def _rename_indexes_after_table_rename(table_name: str, old_prefix: str, new_prefix: str):
    """Renomme tous les index du tableau `table_name` commençant par `old_prefix` → `new_prefix`."""
    bind = op.get_bind()
    dialect = bind.dialect.name  # "mysql" pour MariaDB, "sqlite", "postgresql", etc.

    insp = sa.inspect(bind)
    indexes = insp.get_indexes(table_name)  # [{'name': 'ix_xxx', 'column_names': [...], 'unique': bool}, ...]

    for idx in indexes:
        old_name = idx.get("name")
        if not old_name or not old_name.startswith(old_prefix):
            continue

        new_name = new_prefix + old_name[len(old_prefix):]

        # Essaye d'abord l'API Alembic (gère SQLite/Postgres, et MySQL récents avec table_name)
        try:
            # Alembic >= 1.8 supporte table_name=... pour MySQL
            op.rename_index(old_name, new_name, table_name=table_name)
        except Exception:
            # Fallback SQL brut (utile si une vieille version d'Alembic ne gère pas table_name)
            if dialect == "mysql":  # MariaDB est "mysql" côté SQLAlchemy
                op.execute(sa.text(f"ALTER TABLE `{table_name}` RENAME INDEX `{old_name}` TO `{new_name}`"))
            elif dialect == "sqlite":
                op.execute(sa.text(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"'))
            else:
                # Dernier recours générique (peut ne pas marcher selon le dialecte)
                op.execute(sa.text(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"'))


def upgrade():
    # 1) Renommer la table
    op.rename_table(OLD_TABLE, NEW_TABLE)

    # 2) Renommer les index "ix_forecast_stats_*" -> "ix_weather_data_*"
    _rename_indexes_after_table_rename(NEW_TABLE, OLD_IX_PREFIX, NEW_IX_PREFIX)


def downgrade():
    # Inverse : renomme d'abord les index "ix_weather_data_*" -> "ix_forecast_stats_*"
    _rename_indexes_after_table_rename(NEW_TABLE, NEW_IX_PREFIX, OLD_IX_PREFIX)

    # Puis renomme la table en arrière
    op.rename_table(NEW_TABLE, OLD_TABLE)
