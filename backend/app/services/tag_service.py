"""Service layer for tag operations on notes and todos."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.tag import Tag, NoteTag, TodoTag


async def verify_tags_belong_to_user(
    session: AsyncSession,
    tag_ids: list[UUID],
    user_id: str,
) -> list[Tag]:
    """Verify all tag IDs belong to the user and return tag objects."""
    result = await session.execute(
        select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == UUID(user_id))
    )
    tags = result.scalars().all()

    if len(tags) != len(tag_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more tags not found or don't belong to user"
        )

    return list(tags)


async def attach_tags_to_note(
    session: AsyncSession,
    note_id: UUID,
    tag_ids: list[UUID],
    user_id: str,
) -> None:
    """Attach tags to a note after verifying ownership."""
    if not tag_ids:
        return

    # Verify tags belong to user
    await verify_tags_belong_to_user(session, tag_ids, user_id)

    # Clear existing tags
    await session.execute(
        NoteTag.__table__.delete().where(NoteTag.note_id == note_id)
    )

    # Insert new tag associations
    values = [{"note_id": note_id, "tag_id": tag_id} for tag_id in tag_ids]
    await session.execute(NoteTag.__table__.insert().values(values))


async def attach_tags_to_todo(
    session: AsyncSession,
    todo_id: UUID,
    tag_ids: list[UUID],
    user_id: str,
) -> None:
    """Attach tags to a todo after verifying ownership."""
    if not tag_ids:
        return

    # Verify tags belong to user
    await verify_tags_belong_to_user(session, tag_ids, user_id)

    # Clear existing tags
    await session.execute(
        TodoTag.__table__.delete().where(TodoTag.todo_id == todo_id)
    )

    # Insert new tag associations
    values = [{"todo_id": todo_id, "tag_id": tag_id} for tag_id in tag_ids]
    await session.execute(TodoTag.__table__.insert().values(values))


async def detach_tag_from_note(
    session: AsyncSession,
    note_id: UUID,
    tag_id: UUID,
) -> None:
    """Remove a specific tag from a note."""
    await session.execute(
        NoteTag.__table__.delete().where(
            NoteTag.note_id == note_id,
            NoteTag.tag_id == tag_id,
        )
    )


async def detach_tag_from_todo(
    session: AsyncSession,
    todo_id: UUID,
    tag_id: UUID,
) -> None:
    """Remove a specific tag from a todo."""
    await session.execute(
        TodoTag.__table__.delete().where(
            TodoTag.todo_id == todo_id,
            TodoTag.tag_id == tag_id,
        )
    )
