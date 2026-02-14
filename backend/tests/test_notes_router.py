"""Tests for notes router endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_notes_empty(auth_client: AsyncClient) -> None:
    """List notes returns empty list when no notes exist."""
    response = await auth_client.get("/api/notes/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_note(auth_client: AsyncClient) -> None:
    """Create note returns the new note with ID."""
    payload = {"title": "Test Note", "content": "Test content"}
    response = await auth_client.post("/api/notes/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["content"] == "Test content"
    assert "id" in data
    assert data["is_pinned"] is False
    assert data["is_archived"] is False


@pytest.mark.asyncio
async def test_create_and_list_notes(auth_client: AsyncClient) -> None:
    """Created notes appear in list."""
    # Create two notes
    await auth_client.post("/api/notes/", json={"title": "Note 1", "content": ""})
    await auth_client.post("/api/notes/", json={"title": "Note 2", "content": ""})

    response = await auth_client.get("/api/notes/")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 2


@pytest.mark.asyncio
async def test_get_note_by_id(auth_client: AsyncClient) -> None:
    """Get note by ID returns the note."""
    create_resp = await auth_client.post(
        "/api/notes/", json={"title": "Get Test", "content": "Content"}
    )
    note_id = create_resp.json()["id"]

    response = await auth_client.get(f"/api/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Test"


@pytest.mark.asyncio
async def test_get_note_not_found(auth_client: AsyncClient) -> None:
    """Get non-existent note returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await auth_client.get(f"/api/notes/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_note(auth_client: AsyncClient) -> None:
    """Update note changes fields."""
    create_resp = await auth_client.post(
        "/api/notes/", json={"title": "Original", "content": ""}
    )
    note_id = create_resp.json()["id"]

    response = await auth_client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated", "is_pinned": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["is_pinned"] is True


@pytest.mark.asyncio
async def test_delete_note(auth_client: AsyncClient) -> None:
    """Delete note removes it from list."""
    create_resp = await auth_client.post(
        "/api/notes/", json={"title": "To Delete", "content": ""}
    )
    note_id = create_resp.json()["id"]

    # Delete
    response = await auth_client.delete(f"/api/notes/{note_id}")
    assert response.status_code == 204

    # Verify deleted
    response = await auth_client.get(f"/api/notes/{note_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_filter_notes_by_pinned(auth_client: AsyncClient) -> None:
    """Filter notes by is_pinned works."""
    await auth_client.post("/api/notes/", json={"title": "Pinned", "is_pinned": True})
    await auth_client.post("/api/notes/", json={"title": "Not pinned", "is_pinned": False})

    response = await auth_client.get("/api/notes/", params={"is_pinned": "true"})
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Pinned"


@pytest.mark.asyncio
async def test_filter_notes_by_archived(auth_client: AsyncClient) -> None:
    """Filter notes by is_archived works."""
    # Create note and archive it
    create_resp = await auth_client.post("/api/notes/", json={"title": "Archived"})
    note_id = create_resp.json()["id"]
    await auth_client.put(f"/api/notes/{note_id}", json={"is_archived": True})

    await auth_client.post("/api/notes/", json={"title": "Active"})

    # Filter archived
    response = await auth_client.get("/api/notes/", params={"is_archived": "true"})
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Archived"

    # Filter not archived (default behavior shows non-archived)
    response = await auth_client.get("/api/notes/", params={"is_archived": "false"})
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Active"
