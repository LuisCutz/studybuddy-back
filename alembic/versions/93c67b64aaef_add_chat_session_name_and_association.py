"""add chat session name and association

Revision ID: 93c67b64aaef
Revises: 20dd5cea028d
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '93c67b64aaef'
down_revision: Union[str, Sequence[str], None] = '20dd5cea028d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_session', sa.Column('name', sa.String(length=255), nullable=False, server_default='Nueva sesión'))
    op.create_table(
        'chat_session_document',
        sa.Column('chat_session_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['chat_session_id'], ['chat_session.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('chat_session_id', 'document_id')
    )
    op.add_column('chat_message', sa.Column('created_at', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False))


def downgrade() -> None:
    op.drop_column('chat_message', 'created_at')
    op.drop_table('chat_session_document')
    op.drop_column('chat_session', 'name')
