"""add tenant_id to user and room

Revision ID: 8f6c0f3830c5
Revises: 20dd5cea028d
Create Date: 2026-06-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f6c0f3830c5"
down_revision: Union[str, Sequence[str], None] = "20dd5cea028d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("tenant_id", sa.String(length=100), nullable=False, server_default="default-tenant"))
    op.add_column("study_room", sa.Column("tenant_id", sa.String(length=100), nullable=False, server_default="default-tenant"))


def downgrade() -> None:
    op.drop_column("study_room", "tenant_id")
    op.drop_column("user", "tenant_id")
