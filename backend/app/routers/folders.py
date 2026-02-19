"""Folders router -- CRUD endpoints for note folders."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.folder import Folder
from app.schemas.folder import FolderCreate, FolderResponse, FolderUpdate
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/api/folders", tags=["folders"])


@router.get("/", response_model=PaginatedResponse[FolderResponse])
async def list_folders(
    limit: int = Query(50, ge=1, le=100, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[FolderResponse]:
    """List all folders for the current user as a flat list with pagination."""
    # Get total count
    count_stmt = select(func.count()).select_from(
        select(Folder).where(Folder.user_id == user_id).subquery()
    )
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # Get paginated items
    stmt = (
        select(Folder)
        .where(Folder.user_id == user_id)
        .order_by(Folder.name)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=FolderResponse, status_code=201)
async def create_folder(
    body: FolderCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> FolderResponse:
    """Create a new folder for the current user."""
    folder = Folder(
        user_id=user_id,
        name=body.name,
        parent_id=body.parent_id,
        icon=body.icon,
    )
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return folder


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    body: FolderUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> FolderResponse:
    """Update a folder -- only provided fields are changed."""
    folder = await session.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    if str(folder.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(folder, field, value)

    await session.commit()
    await session.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=204)
async def delete_folder(
    folder_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a folder and cascade to children."""
    folder = await session.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    if str(folder.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await session.delete(folder)
    await session.commit()
