"""Tests for image upload/download endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

# Minimal valid PNG (1x1 pixel)
TEST_PNG_BYTES = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
    0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
    0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
    0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
    0x44, 0xAE, 0x42, 0x60, 0x82
])

MAX_SIZE = 10 * 1024 * 1024  # 10MB for tests


def mock_minio():
    """Create a properly configured minio mock."""
    with patch("app.routers.images.minio_service") as mock:
        mock.max_size = MAX_SIZE
        yield mock


class TestImageUpload:
    """Test image upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_png_success(self, auth_client: AsyncClient):
        """Upload PNG should succeed with 201."""
        with patch("app.routers.images.minio_service") as mock_minio:
            mock_minio.max_size = MAX_SIZE
            mock_minio.upload_image = AsyncMock(
                return_value="users/test/images/abc123.png"
            )

            response = await auth_client.post(
                "/api/images/upload",
                files={"file": ("test.png", TEST_PNG_BYTES, "image/png")},
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert "url" in data
            assert data["content_type"] == "image/png"

    @pytest.mark.asyncio
    async def test_upload_jpeg_success(self, auth_client: AsyncClient):
        """Upload JPEG should succeed."""
        with patch("app.routers.images.minio_service") as mock_minio:
            mock_minio.max_size = MAX_SIZE
            mock_minio.upload_image = AsyncMock(
                return_value="users/test/images/abc123.jpg"
            )

            response = await auth_client.post(
                "/api/images/upload",
                files={"file": ("test.jpg", TEST_PNG_BYTES, "image/jpeg")},
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_upload_heic_success(self, auth_client: AsyncClient):
        """Upload HEIC should succeed."""
        with patch("app.routers.images.minio_service") as mock_minio:
            mock_minio.max_size = MAX_SIZE
            mock_minio.upload_image = AsyncMock(
                return_value="users/test/images/abc123.heic"
            )

            response = await auth_client.post(
                "/api/images/upload",
                files={"file": ("test.heic", TEST_PNG_BYTES, "image/heic")},
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_upload_tiff_success(self, auth_client: AsyncClient):
        """Upload TIFF should succeed."""
        with patch("app.routers.images.minio_service") as mock_minio:
            mock_minio.max_size = MAX_SIZE
            mock_minio.upload_image = AsyncMock(
                return_value="users/test/images/abc123.tiff"
            )

            response = await auth_client.post(
                "/api/images/upload",
                files={"file": ("test.tiff", TEST_PNG_BYTES, "image/tiff")},
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_upload_invalid_content_type(self, auth_client: AsyncClient):
        """Upload with invalid content type should fail with 400."""
        response = await auth_client.post(
            "/api/images/upload",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_octet_stream_rejected(self, auth_client: AsyncClient):
        """Upload with application/octet-stream should fail."""
        response = await auth_client.post(
            "/api/images/upload",
            files={"file": ("test.bin", TEST_PNG_BYTES, "application/octet-stream")},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client: AsyncClient):
        """Upload without auth should fail with 401."""
        response = await client.post(
            "/api/images/upload",
            files={"file": ("test.png", TEST_PNG_BYTES, "image/png")},
        )

        assert response.status_code == 401


class TestAllowedContentTypes:
    """Test that all expected content types are allowed."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "content_type,extension",
        [
            ("image/png", "png"),
            ("image/jpeg", "jpg"),
            ("image/gif", "gif"),
            ("image/webp", "webp"),
            ("image/svg+xml", "svg"),
            ("image/heic", "heic"),
            ("image/heif", "heif"),
            ("image/tiff", "tiff"),
        ],
    )
    async def test_content_type_allowed(
        self, auth_client: AsyncClient, content_type: str, extension: str
    ):
        """All listed content types should be accepted."""
        with patch("app.routers.images.minio_service") as mock_minio:
            mock_minio.max_size = MAX_SIZE
            mock_minio.upload_image = AsyncMock(
                return_value=f"users/test/images/abc.{extension}"
            )

            response = await auth_client.post(
                "/api/images/upload",
                files={"file": (f"test.{extension}", TEST_PNG_BYTES, content_type)},
            )

            assert response.status_code == 201, f"Failed for {content_type}"
