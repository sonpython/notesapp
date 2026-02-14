"""Tests for todos router endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_todos_empty(auth_client: AsyncClient) -> None:
    """List todos returns empty list when no todos exist."""
    response = await auth_client.get("/api/todos/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 50
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_create_todo(auth_client: AsyncClient) -> None:
    """Create todo returns the new todo with ID."""
    payload = {"title": "Test Todo", "description": "Test description"}
    response = await auth_client.post("/api/todos/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "Test description"
    assert "id" in data
    assert data["is_completed"] is False
    assert data["priority"] == 0


@pytest.mark.asyncio
async def test_create_todo_with_priority(auth_client: AsyncClient) -> None:
    """Create todo with priority level."""
    payload = {"title": "High Priority", "priority": 3}
    response = await auth_client.post("/api/todos/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["priority"] == 3


@pytest.mark.asyncio
async def test_toggle_todo_completion(auth_client: AsyncClient) -> None:
    """Toggle todo completion status."""
    # Create todo
    create_resp = await auth_client.post(
        "/api/todos/", json={"title": "Toggle Test"}
    )
    todo_id = create_resp.json()["id"]
    assert create_resp.json()["is_completed"] is False

    # Toggle to completed
    response = await auth_client.post(f"/api/todos/{todo_id}/toggle")
    assert response.status_code == 200
    assert response.json()["is_completed"] is True

    # Toggle back to incomplete
    response = await auth_client.post(f"/api/todos/{todo_id}/toggle")
    assert response.status_code == 200
    assert response.json()["is_completed"] is False


@pytest.mark.asyncio
async def test_delete_todo(auth_client: AsyncClient) -> None:
    """Delete todo removes it."""
    create_resp = await auth_client.post(
        "/api/todos/", json={"title": "To Delete"}
    )
    todo_id = create_resp.json()["id"]

    response = await auth_client.delete(f"/api/todos/{todo_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_filter_todos_by_completion(auth_client: AsyncClient) -> None:
    """Filter todos by is_completed works."""
    # Create completed and incomplete todos
    resp1 = await auth_client.post("/api/todos/", json={"title": "Incomplete"})
    resp2 = await auth_client.post("/api/todos/", json={"title": "Completed"})
    todo_id = resp2.json()["id"]
    await auth_client.post(f"/api/todos/{todo_id}/toggle")

    # Filter incomplete
    response = await auth_client.get("/api/todos/", params={"is_completed": "false"})
    data = response.json()
    assert all(t["is_completed"] is False for t in data["items"])

    # Filter completed
    response = await auth_client.get("/api/todos/", params={"is_completed": "true"})
    data = response.json()
    assert all(t["is_completed"] is True for t in data["items"])
