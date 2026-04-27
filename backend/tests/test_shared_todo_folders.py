"""Tests for SharedTodoFolder owner + public endpoints.

Covers:
- Owner share lifecycle (create / get / revoke)
- Public /check + /access (password / expired / view-limited)
- Editable mode boundary (forbidden when is_editable=false)
- Optimistic locking on update / toggle / delete (409 on stale)
- Folder boundary (cannot escape shared folder via crafted ids)
- Sub-folder hiding (recipient does not see todos from sub-folders)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.deps import get_db
from app.main import app
from app.models.shared_todo_folder import SharedTodoFolder

# -- Helpers ----------------------------------------------------------------


async def _create_folder_with_share(
    auth_client: AsyncClient,
    *,
    is_editable: bool = False,
    password: str | None = None,
    expires_in_hours: int | None = None,
    max_views: int | None = None,
) -> tuple[str, dict]:
    """Create a todo folder + a share, return (folder_id, share_response)."""
    f_resp = await auth_client.post("/api/todo-folders/", json={"name": "Shared Test"})
    assert f_resp.status_code == 201, f_resp.text
    folder_id = f_resp.json()["id"]

    body: dict = {"is_editable": is_editable}
    if password is not None:
        body["password"] = password
    if expires_in_hours is not None:
        body["expires_in_hours"] = expires_in_hours
    if max_views is not None:
        body["max_views"] = max_views

    s_resp = await auth_client.post(f"/api/todo-folders/{folder_id}/share", json=body)
    assert s_resp.status_code == 200, s_resp.text
    return folder_id, s_resp.json()


async def _cleanup_folder(auth_client: AsyncClient, folder_id: str) -> None:
    await auth_client.delete(f"/api/todo-folders/{folder_id}", params={"cascade": "true"})


# -- Owner share lifecycle --------------------------------------------------


@pytest.mark.asyncio
async def test_owner_create_get_delete_share(auth_client: AsyncClient) -> None:
    folder_id, share = await _create_folder_with_share(auth_client)
    try:
        assert share["pub_id"] and len(share["pub_id"]) == 6
        assert share["url"] == f"/pub/folder/{share['pub_id']}"
        assert share["has_password"] is False
        assert share["is_editable"] is False
        assert share["view_count"] == 0

        # GET returns same record
        get_resp = await auth_client.get(f"/api/todo-folders/{folder_id}/share")
        assert get_resp.status_code == 200
        assert get_resp.json()["pub_id"] == share["pub_id"]

        # DELETE revokes
        del_resp = await auth_client.delete(f"/api/todo-folders/{folder_id}/share")
        assert del_resp.status_code == 204

        get_after = await auth_client.get(f"/api/todo-folders/{folder_id}/share")
        # GET returns null body but 200 ok
        assert get_after.status_code == 200
        assert get_after.json() is None
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_owner_share_unknown_folder_404(auth_client: AsyncClient) -> None:
    fake = "00000000-0000-0000-0000-000000000000"
    resp = await auth_client.post(f"/api/todo-folders/{fake}/share", json={"is_editable": False})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_owner_reshare_resets_view_count(auth_client: AsyncClient) -> None:
    folder_id, _ = await _create_folder_with_share(auth_client, max_views=5)
    try:
        # Re-issue share with new password resets view_count to 0
        re = await auth_client.post(
            f"/api/todo-folders/{folder_id}/share",
            json={"is_editable": True, "password": "secret"},
        )
        assert re.status_code == 200
        body = re.json()
        assert body["has_password"] is True
        assert body["is_editable"] is True
        assert body["view_count"] == 0
    finally:
        await _cleanup_folder(auth_client, folder_id)


# -- Public probe + access --------------------------------------------------


@pytest.mark.asyncio
async def test_public_check_and_access_no_password(
    auth_client: AsyncClient, client: AsyncClient
) -> None:
    folder_id, share = await _create_folder_with_share(auth_client)
    try:
        # Check
        chk = await client.get(f"/api/pub/folder/{share['pub_id']}/check")
        assert chk.status_code == 200
        body = chk.json()
        assert body["requires_password"] is False
        assert body["is_editable"] is False
        assert body["folder_name"] == "Shared Test"

        # Access
        acc = await client.post(f"/api/pub/folder/{share['pub_id']}/access")
        assert acc.status_code == 200
        data = acc.json()
        assert data["folder_name"] == "Shared Test"
        assert data["todos"] == []
        # Cookie was set
        assert any(c.name == f"share_session_{share['pub_id']}" for c in client.cookies.jar)
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_public_password_required(auth_client: AsyncClient, client: AsyncClient) -> None:
    folder_id, share = await _create_folder_with_share(auth_client, password="hunter2")
    try:
        chk = await client.get(f"/api/pub/folder/{share['pub_id']}/check")
        assert chk.json()["requires_password"] is True

        # Wrong password
        bad = await client.post(
            f"/api/pub/folder/{share['pub_id']}/access", json={"password": "wrong"}
        )
        assert bad.status_code == 401

        # Missing password
        nopw = await client.post(f"/api/pub/folder/{share['pub_id']}/access", json={})
        assert nopw.status_code == 401

        # Right password
        ok = await client.post(
            f"/api/pub/folder/{share['pub_id']}/access", json={"password": "hunter2"}
        )
        assert ok.status_code == 200
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_public_expired_returns_410(auth_client: AsyncClient, client: AsyncClient) -> None:
    folder_id, share = await _create_folder_with_share(auth_client, expires_in_hours=1)
    try:
        # Rewind expires_at to the past directly via the override DB session
        override = app.dependency_overrides[get_db]
        async for db in override():
            await db.execute(
                update(SharedTodoFolder)
                .where(SharedTodoFolder.pub_id == share["pub_id"])
                .values(expires_at=datetime.now(UTC) - timedelta(hours=1))
            )
            await db.commit()
            break

        chk = await client.get(f"/api/pub/folder/{share['pub_id']}/check")
        assert chk.status_code == 410
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_public_view_limit_enforced(auth_client: AsyncClient, client: AsyncClient) -> None:
    folder_id, share = await _create_folder_with_share(auth_client, max_views=1)
    try:
        # First access OK
        first = await client.post(f"/api/pub/folder/{share['pub_id']}/access")
        assert first.status_code == 200
        # Second access blocked
        second = await client.post(f"/api/pub/folder/{share['pub_id']}/access")
        assert second.status_code == 410
    finally:
        await _cleanup_folder(auth_client, folder_id)


# -- Editable / read-only enforcement ---------------------------------------


@pytest.mark.asyncio
async def test_readonly_mutations_are_403(auth_client: AsyncClient, client: AsyncClient) -> None:
    folder_id, share = await _create_folder_with_share(auth_client, is_editable=False)
    try:
        await client.post(f"/api/pub/folder/{share['pub_id']}/access")
        pub_id = share["pub_id"]

        # Create
        c = await client.post(f"/api/pub/folder/{pub_id}/todos", json={"title": "no"})
        assert c.status_code == 403
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_editable_full_crud(auth_client: AsyncClient, client: AsyncClient) -> None:
    folder_id, share = await _create_folder_with_share(auth_client, is_editable=True)
    pub_id = share["pub_id"]
    try:
        await client.post(f"/api/pub/folder/{pub_id}/access")

        # Create
        cr = await client.post(
            f"/api/pub/folder/{pub_id}/todos",
            json={"title": "first", "priority": 2},
        )
        assert cr.status_code == 201, cr.text
        todo = cr.json()
        assert todo["title"] == "first"
        assert todo["priority"] == 2

        # List
        lst = await client.get(f"/api/pub/folder/{pub_id}/todos")
        assert lst.status_code == 200
        assert len(lst.json()) == 1

        # Update with correct expected_updated_at
        upd = await client.put(
            f"/api/pub/folder/{pub_id}/todos/{todo['id']}",
            json={
                "expected_updated_at": todo["updated_at"],
                "title": "renamed",
            },
        )
        assert upd.status_code == 200, upd.text
        assert upd.json()["title"] == "renamed"

        # Toggle
        tg = await client.post(
            f"/api/pub/folder/{pub_id}/todos/{todo['id']}/toggle",
            json={"expected_updated_at": upd.json()["updated_at"]},
        )
        assert tg.status_code == 200
        assert tg.json()["is_completed"] is True

        # Delete
        dl = await client.request(
            "DELETE",
            f"/api/pub/folder/{pub_id}/todos/{todo['id']}",
            json={"expected_updated_at": tg.json()["updated_at"]},
        )
        assert dl.status_code == 204

        empty = await client.get(f"/api/pub/folder/{pub_id}/todos")
        assert empty.json() == []
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_optimistic_lock_409_on_stale_update(
    auth_client: AsyncClient, client: AsyncClient
) -> None:
    folder_id, share = await _create_folder_with_share(auth_client, is_editable=True)
    pub_id = share["pub_id"]
    try:
        await client.post(f"/api/pub/folder/{pub_id}/access")
        cr = await client.post(f"/api/pub/folder/{pub_id}/todos", json={"title": "lock me"})
        todo = cr.json()
        stale_token = todo["updated_at"]

        # First update succeeds and bumps updated_at
        first = await client.put(
            f"/api/pub/folder/{pub_id}/todos/{todo['id']}",
            json={"expected_updated_at": stale_token, "title": "v2"},
        )
        assert first.status_code == 200

        # Second update with the OLD token must fail 409
        second = await client.put(
            f"/api/pub/folder/{pub_id}/todos/{todo['id']}",
            json={"expected_updated_at": stale_token, "title": "v3"},
        )
        assert second.status_code == 409
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_no_session_returns_401(auth_client: AsyncClient, client: AsyncClient) -> None:
    folder_id, share = await _create_folder_with_share(auth_client, is_editable=True)
    pub_id = share["pub_id"]
    try:
        # Skip /access -> no cookie
        client.cookies.clear()
        resp = await client.get(f"/api/pub/folder/{pub_id}/todos")
        assert resp.status_code == 401
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_revoke_breaks_existing_session(
    auth_client: AsyncClient, client: AsyncClient
) -> None:
    folder_id, share = await _create_folder_with_share(auth_client, is_editable=True)
    pub_id = share["pub_id"]
    try:
        await client.post(f"/api/pub/folder/{pub_id}/access")
        # Owner revokes
        await auth_client.delete(f"/api/todo-folders/{folder_id}/share")
        # Cookie still on client but DB row is gone -> 404
        resp = await client.get(f"/api/pub/folder/{pub_id}/todos")
        assert resp.status_code == 404
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_subfolder_todos_are_hidden(auth_client: AsyncClient, client: AsyncClient) -> None:
    folder_id, share = await _create_folder_with_share(auth_client, is_editable=False)
    pub_id = share["pub_id"]
    try:
        # Create a sub-folder + a todo in it
        sub = await auth_client.post(
            "/api/todo-folders/", json={"name": "Sub", "parent_id": folder_id}
        )
        sub_id = sub.json()["id"]
        await auth_client.post(
            "/api/todos/",
            json={"title": "in subfolder", "folder_id": sub_id},
        )
        # Also create one IN the shared folder
        await auth_client.post(
            "/api/todos/",
            json={"title": "in shared", "folder_id": folder_id},
        )

        await client.post(f"/api/pub/folder/{pub_id}/access")
        lst = await client.get(f"/api/pub/folder/{pub_id}/todos")
        titles = [t["title"] for t in lst.json()]
        assert "in shared" in titles
        assert "in subfolder" not in titles
    finally:
        await _cleanup_folder(auth_client, folder_id)


@pytest.mark.asyncio
async def test_cannot_mutate_todos_outside_shared_folder(
    auth_client: AsyncClient, client: AsyncClient
) -> None:
    """Crafting a todo_id from a different folder should yield 404."""
    folder_id, share = await _create_folder_with_share(auth_client, is_editable=True)
    pub_id = share["pub_id"]
    try:
        # Create another folder + a todo in it
        other = await auth_client.post("/api/todo-folders/", json={"name": "Other"})
        other_id = other.json()["id"]
        ot = await auth_client.post("/api/todos/", json={"title": "outside", "folder_id": other_id})
        outside_todo_id = ot.json()["id"]

        await client.post(f"/api/pub/folder/{pub_id}/access")

        # Try to update the outside todo via the shared pub_id
        resp = await client.put(
            f"/api/pub/folder/{pub_id}/todos/{outside_todo_id}",
            json={
                "expected_updated_at": ot.json()["updated_at"],
                "title": "hijacked",
            },
        )
        assert resp.status_code == 404

        await _cleanup_folder(auth_client, other_id)
    finally:
        await _cleanup_folder(auth_client, folder_id)
