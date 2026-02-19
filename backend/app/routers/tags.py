"""API endpoints for tag CRUD operations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("/", response_model=list[TagResponse])
async def list_tags(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """List all tags for the current user."""
    result = await session.execute(
        select(Tag)
        .where(Tag.user_id == UUID(user_id))
        .order_by(Tag.name)
    )
    tags = result.scalars().all()
    return tags


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    body: TagCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Create a new tag."""
    tag = Tag(
        user_id=UUID(user_id),
        name=body.name,
        color=body.color,
    )

    session.add(tag)

    try:
        await session.commit()
        await session.refresh(tag)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag with name '{body.name}' already exists"
        )

    return tag


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    body: TagUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Update an existing tag's name or color."""
    # Fetch tag
    result = await session.execute(
        select(Tag).where(Tag.id == tag_id)
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Verify ownership
    if str(tag.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Apply updates
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    try:
        await session.commit()
        await session.refresh(tag)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag with name '{body.name}' already exists"
        )

    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Delete a tag (cascades from junction tables)."""
    # Fetch tag
    result = await session.execute(
        select(Tag).where(Tag.id == tag_id)
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Verify ownership
    if str(tag.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete (cascades via ondelete="CASCADE" in junction tables)
    await session.delete(tag)
    await session.commit()
