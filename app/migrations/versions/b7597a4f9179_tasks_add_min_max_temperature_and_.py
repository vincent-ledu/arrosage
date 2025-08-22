"""tasks: add min/max temperature and precipitation when watering

Revision ID: b7597a4f9179
Revises: add_created_updated_drop_start_time
Create Date: 2025-08-22 14:10:49.940620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_min_max_temperature_and_precipitation'
down_revision: Union[str, Sequence[str], None] = 'add_created_updated_drop_start_time'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  # 1) Add the columns as nullable first
  with op.batch_alter_table("tasks") as batch_op:
    batch_op.add_column(sa.Column("min_temp", sa.Float(), nullable=True))
    batch_op.add_column(sa.Column("max_temp", sa.Float(), nullable=True))
    batch_op.add_column(sa.Column("precipitation", sa.Float(), nullable=True))


def downgrade() -> None:
  with op.batch_alter_table("tasks") as batch_op:
    batch_op.drop_column("min_temp")  
    batch_op.drop_column("max_temp")  
    batch_op.drop_column("precipitation")  
