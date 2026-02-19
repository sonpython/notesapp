"""MinIO storage service for image uploads."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from io import BytesIO

from miniopy_async import Minio
from miniopy_async.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = frozenset(
    [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
    ]
)

CONTENT_TYPE_TO_EXT = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/svg+xml": "svg",
}


class MinioStorageService:
    """Async MinIO client wrapper for image storage."""

    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket = settings.MINIO_BUCKET
        self.max_size = settings.MINIO_MAX_IMAGE_SIZE

    async def ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            exists = await self.client.bucket_exists(self.bucket)
            if not exists:
                await self.client.make_bucket(self.bucket)
                logger.info(f"Created MinIO bucket: {self.bucket}")
            else:
                logger.info(f"MinIO bucket exists: {self.bucket}")
        except S3Error as e:
            logger.error(f"Failed to ensure bucket: {e}")
            raise

    def _build_object_key(self, user_id: str, image_id: str, ext: str) -> str:
        """Build object key: users/{user_id}/images/{image_id}.{ext}"""
        return f"users/{user_id}/images/{image_id}.{ext}"

    async def upload_image(
        self,
        user_id: str,
        file_data: bytes,
        content_type: str,
        original_filename: str,
    ) -> str:
        """Upload image and return object key.

        Raises:
            ValueError: If content type not allowed or file too large.
        """
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Content type not allowed: {content_type}")

        if len(file_data) > self.max_size:
            raise ValueError(f"File too large: {len(file_data)} > {self.max_size}")

        ext = CONTENT_TYPE_TO_EXT.get(content_type, "bin")
        image_id = str(uuid.uuid4())
        object_key = self._build_object_key(user_id, image_id, ext)

        await self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_key,
            data=BytesIO(file_data),
            length=len(file_data),
            content_type=content_type,
        )
        logger.info(f"Uploaded image: {object_key}")
        return object_key

    async def get_image(self, object_key: str) -> AsyncGenerator[bytes, None]:
        """Stream image data from MinIO."""
        response = await self.client.get_object(self.bucket, object_key)
        try:
            async for chunk in response.content.iter_chunked(8192):
                yield chunk
        finally:
            response.close()
            await response.release()

    async def get_image_bytes(self, object_key: str) -> bytes:
        """Get image as bytes (for smaller images)."""
        response = await self.client.get_object(self.bucket, object_key)
        try:
            return await response.read()
        finally:
            response.close()
            await response.release()

    async def get_image_info(self, object_key: str) -> dict:
        """Get object metadata (content_type, size, etc)."""
        try:
            stat = await self.client.stat_object(self.bucket, object_key)
            return {
                "content_type": stat.content_type,
                "size": stat.size,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
            }
        except S3Error:
            return {}

    async def delete_image(self, object_key: str) -> None:
        """Delete image from MinIO."""
        await self.client.remove_object(self.bucket, object_key)
        logger.info(f"Deleted image: {object_key}")

    async def list_user_images(self, user_id: str) -> list[dict]:
        """List all images for a user."""
        prefix = f"users/{user_id}/images/"
        objects = await self.client.list_objects(self.bucket, prefix=prefix)

        result = []
        for obj in objects:
            result.append(
                {
                    "key": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                }
            )
        return result

    async def find_user_image(self, user_id: str, image_id: str) -> str | None:
        """Find image by user_id and image_id (handles any extension)."""
        prefix = f"users/{user_id}/images/{image_id}."
        objects = await self.client.list_objects(self.bucket, prefix=prefix)

        for obj in objects:
            return obj.object_name
        return None


# Global instance
minio_service = MinioStorageService()
