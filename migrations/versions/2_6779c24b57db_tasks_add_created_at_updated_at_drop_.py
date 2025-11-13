"""tasks: add created_at/updated_at, drop start_time

Revision ID: 6779c24b57db
Revises: a56e0b3d45ab
Create Date: 2025-08-21 18:16:43.904218

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6779c24b57db"
down_revision: Union[str, Sequence[str], None] = "a56e0b3d45ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Add the columns as nullable first
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)
        )

    # 2) Backfill: populate created_at/updated_at from start_time (epoch)
    conn = op.get_bind()
    # SQLite: datetime(<epoch>, 'unixepoch') -> 'YYYY-MM-DD HH:MM:SS'
    conn.execute(
        sa.text("""
        UPDATE tasks
        SET created_at = from_unixtime(start_time),
            updated_at = from_unixtime(start_time + duration)
        WHERE created_at IS NULL OR updated_at IS NULL
    """)
    )

    # 3) Set NOT NULL + index (Alembic will create indexes if they don't exist)
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
        )
        batch_op.create_index("ix_tasks_status", ["status"], unique=False)

    # 4) Remove start_time
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_index("ix_tasks_start_time")
        batch_op.drop_column("start_time")


def downgrade() -> None:
    # 1) Recreate start_time (epoch)
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("start_time", sa.Integer(), nullable=True))

    # 2) Inverse backfill: restore start_time from created_at
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        UPDATE tasks
        SET start_time = CAST(strftime('%s', created_at) AS INTEGER)
        WHERE start_time IS NULL
    """)
    )

    # 3) Remove created_at / updated_at
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")

    # 4) Set start_time NOT NULL if you want (according to your previous schema)
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column("start_time", nullable=False)

    # 5) Recreate the index on start_time
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.create_index("ix_tasks_start_time", ["start_time"])

    # 6) Remove the index on status if necessary
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_index("ix_tasks_status", if_exists=True)
