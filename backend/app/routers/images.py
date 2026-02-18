"""Images router -- upload, serve, delete image files via MinIO."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse

from app.deps import get_current_user
from app.schemas.image import ImageListItem, ImageUploadResponse
from app.services.minio_storage_service import minio_service, ALLOWED_CONTENT_TYPES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["images"])


def _extract_image_id(object_key: str) -> str:
    """Extract image ID from object key (users/{uid}/images/{id}.{ext})."""
    filename = object_key.rsplit("/", 1)[-1]
    return filename.rsplit(".", 1)[0]


@router.post("/upload", response_model=ImageUploadResponse, status_code=201)
async def upload_image(
    file: UploadFile,
    user_id: str = Depends(get_current_user),
) -> ImageUploadResponse:
    """Upload an image file. Max 10MB, allowed: jpeg/png/gif/webp/svg."""
    # Validate content type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {content_type}. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # Read file into memory and validate size
    file_data = await file.read()
    max_size = minio_service.max_size

    if len(file_data) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(file_data)} bytes. Max: {max_size} bytes",
        )

    # Upload to MinIO
    try:
        object_key = await minio_service.upload_image(
            user_id=user_id,
            file_data=file_data,
            content_type=content_type,
            original_filename=file.filename or "image",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Image upload failed")
        raise HTTPException(status_code=500, detail="Upload failed")

    image_id = _extract_image_id(object_key)

    return ImageUploadResponse(
        id=image_id,
        url=f"/api/images/{image_id}",
        filename=file.filename or "image",
        content_type=content_type,
        size=len(file_data),
    )


@router.get("/{image_id}")
async def get_image(
    image_id: str,
    user_id: str = Depends(get_current_user),
) -> Response:
    """Serve an image by ID. Proxies from MinIO with caching headers."""
    # Find the object key (handles any extension)
    object_key = await minio_service.find_user_image(user_id, image_id)

    if not object_key:
        raise HTTPException(status_code=404, detail="Image not found")

    # Get metadata for content-type
    info = await minio_service.get_image_info(object_key)
    if not info:
        raise HTTPException(status_code=404, detail="Image not found")

    content_type = info.get("content_type", "application/octet-stream")

    # Stream the image
    return StreamingResponse(
        minio_service.get_image(object_key),
        media_type=content_type,
        headers={
            "Cache-Control": "private, max-age=86400",  # 1 day
        },
    )


@router.delete("/{image_id}", status_code=204)
async def delete_image(
    image_id: str,
    user_id: str = Depends(get_current_user),
) -> None:
    """Delete an image by ID."""
    object_key = await minio_service.find_user_image(user_id, image_id)

    if not object_key:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        await minio_service.delete_image(object_key)
    except Exception:
        logger.exception("Image deletion failed")
        raise HTTPException(status_code=500, detail="Delete failed")


@router.get("/", response_model=list[ImageListItem])
async def list_images(
    user_id: str = Depends(get_current_user),
) -> list[ImageListItem]:
    """List all images for the current user."""
    images = await minio_service.list_user_images(user_id)

    return [
        ImageListItem(
            id=_extract_image_id(img["key"]),
            url=f"/api/images/{_extract_image_id(img['key'])}",
            size=img["size"],
            last_modified=img.get("last_modified"),
        )
        for img in images
    ]
