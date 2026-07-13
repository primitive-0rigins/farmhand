"""add farm manual tasks

Revision ID: 8f3e8f7b6e0a
Revises: ed6722bc329f
Create Date: 2026-07-13 13:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "8f3e8f7b6e0a"
down_revision = "ed6722bc329f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "farm_manual_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_farm_manual_tasks_farm_id"), "farm_manual_tasks", ["farm_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_farm_manual_tasks_farm_id"), table_name="farm_manual_tasks")
    op.drop_table("farm_manual_tasks")
