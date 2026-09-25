"""Change Twin migration: change_records table.

Revision ID: 004
Revises: 003
Create Date: 2026-09-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "change_records",
        sa.Column("id", mysql.CHAR(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("branch", sa.String(100), nullable=True),
        sa.Column("author", sa.String(100), nullable=True),
        sa.Column("git_diff", sa.Text(), nullable=False),
        sa.Column("direct_impact_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indirect_impact_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_level", sa.String(50), nullable=False, server_default="low"),
        sa.Column("impact_summary", sa.JSON(), nullable=False),
        sa.Column("repository_id", mysql.CHAR(36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_change_records_title", "change_records", ["title"])
    op.create_index("ix_change_records_repository_id", "change_records", ["repository_id"])


def downgrade() -> None:
    op.drop_table("change_records")
