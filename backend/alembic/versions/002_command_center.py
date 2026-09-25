"""Command center migration: repositories, services, findings, activities tables.

Revision ID: 002
Revises: 001
Create Date: 2026-09-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create repositories table
    op.create_table(
        "repositories",
        sa.Column("id", mysql.CHAR(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("default_branch", sa.String(100), server_default="main", nullable=False),
        sa.Column("language", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), server_default="active", nullable=False),
        sa.Column("project_id", mysql.CHAR(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_repositories_name", "repositories", ["name"])
    op.create_index("ix_repositories_project_id", "repositories", ["project_id"])

    # Create services table
    op.create_table(
        "services",
        sa.Column("id", mysql.CHAR(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("service_type", sa.String(50), server_default="api", nullable=False),
        sa.Column("status", sa.String(50), server_default="healthy", nullable=False),
        sa.Column("runtime", sa.String(100), nullable=True),
        sa.Column("version", sa.String(50), server_default="v1.0.0", nullable=False),
        sa.Column(
            "repository_id", mysql.CHAR(36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_services_name", "services", ["name"])
    op.create_index("ix_services_repository_id", "services", ["repository_id"])

    # Create findings table
    op.create_table(
        "findings",
        sa.Column("id", mysql.CHAR(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("finding_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), server_default="medium", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_payload", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), server_default="open", nullable=False),
        sa.Column(
            "repository_id", mysql.CHAR(36), sa.ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("service_id", mysql.CHAR(36), sa.ForeignKey("services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_findings_title", "findings", ["title"])
    op.create_index("ix_findings_finding_type", "findings", ["finding_type"])
    op.create_index("ix_findings_severity", "findings", ["severity"])
    op.create_index("ix_findings_status", "findings", ["status"])

    # Create activities table
    op.create_table(
        "activities",
        sa.Column("id", mysql.CHAR(36), primary_key=True),
        sa.Column("actor", sa.String(100), server_default="system", nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("metadata_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activities_action", "activities", ["action"])
    op.create_index("ix_activities_entity_type", "activities", ["entity_type"])


def downgrade() -> None:
    op.drop_table("activities")
    op.drop_table("findings")
    op.drop_table("services")
    op.drop_table("repositories")
