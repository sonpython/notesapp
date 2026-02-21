"""add_shared_notes_table

Revision ID: dd2fff4b4ecd
Revises: 517054383db8
Create Date: 2026-02-19 01:00:49.716288+00:00
"""
from __future__ import annotations
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "dd2fff4b4ecd"
down_revision: Union[str, None] = "517054383db8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "shared_notes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("note_id", sa.UUID(), sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("share_token", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("is_public", sa.Boolean(), default=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("view_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("shared_notes")
