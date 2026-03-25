"""add todo_folders table and folder_id to todos

Revision ID: e9fe7574f58c
Revises: dd2fff4b4ecd
Create Date: 2026-03-25 20:29:26.105088+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9fe7574f58c'
down_revision: Union[str, None] = 'dd2fff4b4ecd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create todo_folders table
    op.create_table('todo_folders',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('parent_id', sa.Uuid(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['todo_folders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_todo_folders_parent_id'), 'todo_folders', ['parent_id'], unique=False)
    op.create_index(op.f('ix_todo_folders_user_id'), 'todo_folders', ['user_id'], unique=False)

    # 2. Add folder_id column to todos
    op.add_column('todos', sa.Column('folder_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_todos_folder_id'), 'todos', ['folder_id'], unique=False)
    op.create_foreign_key('fk_todos_folder_id', 'todos', 'todo_folders', ['folder_id'], ['id'], ondelete='SET NULL')

    # 3. Data migration: create "Personal" folder per user, assign todos
    conn = op.get_bind()
    user_ids = conn.execute(sa.text("SELECT DISTINCT user_id FROM todos")).fetchall()
    for (uid,) in user_ids:
        result = conn.execute(
            sa.text(
                "INSERT INTO todo_folders (user_id, name, sort_order) "
                "VALUES (:uid, 'Personal', 0) RETURNING id"
            ),
            {"uid": uid},
        )
        folder_id = result.fetchone()[0]
        conn.execute(
            sa.text("UPDATE todos SET folder_id = :fid WHERE user_id = :uid"),
            {"fid": folder_id, "uid": uid},
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_todos_folder_id', 'todos', type_='foreignkey')
    op.drop_index(op.f('ix_todos_folder_id'), table_name='todos')
    op.drop_column('todos', 'folder_id')
    op.drop_index(op.f('ix_todo_folders_user_id'), table_name='todo_folders')
    op.drop_index(op.f('ix_todo_folders_parent_id'), table_name='todo_folders')
    op.drop_table('todo_folders')
