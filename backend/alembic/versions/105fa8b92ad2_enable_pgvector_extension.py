"""enable pgvector extension

Revision ID: 105fa8b92ad2
Revises: e72d235fc2ea
Create Date: 2026-05-03 13:52:24.331051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '105fa8b92ad2'
down_revision: Union[str, Sequence[str], None] = 'e72d235fc2ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")



def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS vector")

