"""add_unaccent_extension

Revision ID: 517054383db8
Revises: 7239f9a284c6
Create Date: 2026-02-19 00:22:28.669139+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '517054383db8'
down_revision: Union[str, None] = '7239f9a284c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Install unaccent extension for Vietnamese diacritics search."""
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    """Remove unaccent extension."""
    op.execute("DROP EXTENSION IF EXISTS unaccent")
