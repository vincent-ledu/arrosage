"""baseline (no-op)

Revision ID: a56e0b3d45ab
Revises:
Create Date: 2025-08-19 01:32:21.405920

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a56e0b3d45ab"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("duration", sa.INTEGER(), nullable=False),
        sa.Column("start_time", sa.Integer()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_start_time"), "tasks", ["start_time"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    pass
