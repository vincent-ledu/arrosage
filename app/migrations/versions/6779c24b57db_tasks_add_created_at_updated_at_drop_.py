"""tasks: add created_at/updated_at, drop start_time

Revision ID: 6779c24b57db
Revises: a56e0b3d45ab
Create Date: 2025-08-21 18:16:43.904218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_created_updated_drop_start_time'
down_revision: Union[str, Sequence[str], None] = 'a56e0b3d45ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1) Ajouter les colonnes en nullable d'abord
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    # 2) Backfill: remplir created_at/updated_at depuis start_time (epoch)
    conn = op.get_bind()
    # SQLite: datetime(<epoch>, 'unixepoch') -> 'YYYY-MM-DD HH:MM:SS'
    conn.execute(sa.text("""
        UPDATE tasks
        SET created_at = datetime(start_time, 'unixepoch'),
            updated_at = datetime(start_time + duration, 'unixepoch')
        WHERE created_at IS NULL OR updated_at IS NULL
    """))

    # 3) NOT NULL + index (Alembic créera les index si non existants)
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column("created_at", existing_type=sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"))
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"))
        # Si besoin d'ajouter explicitement des index nommés (souvent auto via autogenerate)
        # batch_op.create_index("ix_tasks_created_at", ["created_at"])
        # batch_op.create_index("ix_tasks_updated_at", ["updated_at"])
        batch_op.create_index("ix_tasks_status", ["status"], unique=False)

    # 4) Supprimer start_time
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_index("ix_tasks_start_time")
        batch_op.drop_column("start_time")


def downgrade() -> None:
    # 1) Recréer start_time (epoch)
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("start_time", sa.Integer(), nullable=True))

    # 2) Backfill inverse: remettre start_time depuis created_at
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE tasks
        SET start_time = CAST(strftime('%s', created_at) AS INTEGER)
        WHERE start_time IS NULL
    """))

    # 3) Supprimer created_at / updated_at
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")

    # 4) Rendre start_time NOT NULL si tu le souhaites (selon ton ancien schéma)
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column("start_time", nullable=False)
    
    # 5) Recréer l'index sur start_time
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.create_index("ix_tasks_start_time", ["start_time"])

    # 6) Supprimer l'index sur status si nécessaire
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_index("ix_tasks_status", if_exists=True)