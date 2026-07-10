"""Merge de migraciones develop y chat

Revision ID: a139a815175c
Revises: 93c67b64aaef, bbf464fa9cfd
Create Date: 2026-07-10 16:18:34.245565

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a139a815175c'
down_revision: Union[str, Sequence[str], None] = ('93c67b64aaef', 'bbf464fa9cfd')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
