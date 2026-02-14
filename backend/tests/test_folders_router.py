"""Tests for folders router endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_folders_empty(auth_client: AsyncClient) -> None:
    """List folders returns empty list when no folders exist."""
    response = await auth_client.get("/api/folders/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_folder(auth_client: AsyncClient) -> None:
    """Create folder returns the new folder with ID."""
    payload = {"name": "Test Folder"}
    response = await auth_client.post("/api/folders/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Folder"
    assert "id" in data
    assert data["parent_id"] is None


@pytest.mark.asyncio
async def test_create_nested_folder(auth_client: AsyncClient) -> None:
    """Create nested folder with parent."""
    # Create parent
    parent_resp = await auth_client.post(
        "/api/folders/", json={"name": "Parent"}
    )
    parent_id = parent_resp.json()["id"]

    # Create child
    child_resp = await auth_client.post(
        "/api/folders/", json={"name": "Child", "parent_id": parent_id}
    )
    assert child_resp.status_code == 201
    assert child_resp.json()["parent_id"] == parent_id


@pytest.mark.asyncio
async def test_rename_folder(auth_client: AsyncClient) -> None:
    """Rename folder updates name."""
    create_resp = await auth_client.post(
        "/api/folders/", json={"name": "Original"}
    )
    folder_id = create_resp.json()["id"]

    response = await auth_client.put(
        f"/api/folders/{folder_id}",
        json={"name": "Renamed"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


@pytest.mark.asyncio
async def test_delete_folder(auth_client: AsyncClient) -> None:
    """Delete folder removes it."""
    create_resp = await auth_client.post(
        "/api/folders/", json={"name": "To Delete"}
    )
    folder_id = create_resp.json()["id"]

    response = await auth_client.delete(f"/api/folders/{folder_id}")
    assert response.status_code == 204

    # Verify deleted
    list_resp = await auth_client.get("/api/folders/")
    folder_ids = [f["id"] for f in list_resp.json()]
    assert folder_id not in folder_ids


@pytest.mark.asyncio
async def test_folder_not_found(auth_client: AsyncClient) -> None:
    """Operations on non-existent folder return 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await auth_client.put(
        f"/api/folders/{fake_id}", json={"name": "Test"}
    )
    assert response.status_code == 404

    response = await auth_client.delete(f"/api/folders/{fake_id}")
    assert response.status_code == 404
