"""Initial migration: organizations and projects tables.

Revision ID: 001
Revises:
Create Date: 2026-09-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", mysql.CHAR(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"])

    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", mysql.CHAR(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "organization_id", mysql.CHAR(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_name", "projects", ["name"])
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_projects_organization_id", table_name="projects")
    op.drop_index("ix_projects_name", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_table("organizations")
