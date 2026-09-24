"""Reality Graph migration: graph_nodes and graph_edges tables.

Revision ID: 003
Revises: 002
Create Date: 2026-09-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: str | None = '002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create graph_nodes table
    op.create_table(
        'graph_nodes',
        sa.Column('id', mysql.CHAR(36), primary_key=True),
        sa.Column('node_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('path', sa.String(1024), nullable=True),
        sa.Column('properties', sa.JSON(), nullable=False),
        sa.Column('repository_id', mysql.CHAR(36), sa.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_graph_nodes_node_type', 'graph_nodes', ['node_type'])
    op.create_index('ix_graph_nodes_name', 'graph_nodes', ['name'])
    op.create_index('ix_graph_nodes_repository_id', 'graph_nodes', ['repository_id'])

    # Create graph_edges table
    op.create_table(
        'graph_edges',
        sa.Column('id', mysql.CHAR(36), primary_key=True),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('properties', sa.JSON(), nullable=False),
        sa.Column('source_node_id', mysql.CHAR(36), sa.ForeignKey('graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_node_id', mysql.CHAR(36), sa.ForeignKey('graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_graph_edges_relationship_type', 'graph_edges', ['relationship_type'])
    op.create_index('ix_graph_edges_source_node_id', 'graph_edges', ['source_node_id'])
    op.create_index('ix_graph_edges_target_node_id', 'graph_edges', ['target_node_id'])


def downgrade() -> None:
    op.drop_table('graph_edges')
    op.drop_table('graph_nodes')
