"""Create device snapshot and command logs.

Revision ID: 0f1caa2f4cbb
Revises: b4289ac7f46f
Create Date: 2025-12-17

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0f1caa2f4cbb"
down_revision: Union[str, Sequence[str], None] = "b4289ac7f46f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "device_snapshot",
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("water_level_percent", sa.Integer(), nullable=True),
        sa.Column("watering", sa.Boolean(), nullable=True),
        sa.Column("remaining_sec", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("device_id"),
    )
    op.create_index(
        op.f("ix_device_snapshot_last_seen_at"),
        "device_snapshot",
        ["last_seen_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_snapshot_status"),
        "device_snapshot",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_snapshot_updated_at"),
        "device_snapshot",
        ["updated_at"],
        unique=False,
    )

    op.create_table(
        "device_command_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column("command", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_device_command_log_command"),
        "device_command_log",
        ["command"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_command_log_created_at"),
        "device_command_log",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_command_log_device_id"),
        "device_command_log",
        ["device_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_command_log_result"),
        "device_command_log",
        ["result"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_device_command_log_result"), table_name="device_command_log")
    op.drop_index(op.f("ix_device_command_log_device_id"), table_name="device_command_log")
    op.drop_index(op.f("ix_device_command_log_created_at"), table_name="device_command_log")
    op.drop_index(op.f("ix_device_command_log_command"), table_name="device_command_log")
    op.drop_table("device_command_log")

    op.drop_index(op.f("ix_device_snapshot_updated_at"), table_name="device_snapshot")
    op.drop_index(op.f("ix_device_snapshot_status"), table_name="device_snapshot")
    op.drop_index(op.f("ix_device_snapshot_last_seen_at"), table_name="device_snapshot")
    op.drop_table("device_snapshot")

