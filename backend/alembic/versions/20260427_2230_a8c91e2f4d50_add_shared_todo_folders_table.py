"""add_shared_todo_folders_table

Revision ID: a8c91e2f4d50
Revises: 746b14aad348
Create Date: 2026-04-27 22:30:00.000000+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a8c91e2f4d50"
down_revision: str | None = "746b14aad348"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shared_todo_folders",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "todo_folder_id",
            sa.Uuid(),
            sa.ForeignKey("todo_folders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pub_id", sa.String(length=6), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_views", sa.Integer(), nullable=True),
        sa.Column(
            "view_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_editable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_shared_todo_folders_pub_id",
        "shared_todo_folders",
        ["pub_id"],
        unique=True,
    )
    op.create_index(
        "uq_shared_todo_folders_folder",
        "shared_todo_folders",
        ["todo_folder_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_shared_todo_folders_folder", table_name="shared_todo_folders")
    op.drop_index("ix_shared_todo_folders_pub_id", table_name="shared_todo_folders")
    op.drop_table("shared_todo_folders")
