"""Tests for note export endpoints (markdown, PDF, ZIP)."""

from __future__ import annotations

import io
import zipfile
from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_export_note_markdown(
    auth_client: AsyncClient,
) -> None:
    """Test exporting a single note as markdown."""
    # Create a test note
    create_response = await auth_client.post(
        "/api/notes/",
        json={"title": "Test Note", "content": "This is test content"},
    )
    assert create_response.status_code == 201
    note = create_response.json()

    # Export as markdown
    response = await auth_client.get(f"/api/notes/{note['id']}/export/md")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]

    content = response.text
    assert "Test Note" in content
    assert "This is test content" in content
    assert "Created:" in content
    assert "Updated:" in content


@pytest.mark.asyncio
async def test_export_note_markdown_not_found(
    auth_client: AsyncClient,
) -> None:
    """Test exporting non-existent note returns 404."""
    fake_id = uuid4()
    response = await auth_client.get(f"/api/notes/{fake_id}/export/md")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_note_pdf(
    auth_client: AsyncClient,
) -> None:
    """Test exporting a single note as PDF."""
    # Create a test note
    create_response = await auth_client.post(
        "/api/notes/",
        json={"title": "PDF Test", "content": "Content for PDF export"},
    )
    assert create_response.status_code == 201
    note = create_response.json()

    # Export as PDF
    response = await auth_client.get(f"/api/notes/{note['id']}/export/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]

    # Verify PDF magic bytes
    content = response.content
    assert content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_export_note_pdf_not_found(
    auth_client: AsyncClient,
) -> None:
    """Test exporting non-existent note as PDF returns 404."""
    fake_id = uuid4()
    response = await auth_client.get(f"/api/notes/{fake_id}/export/pdf")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_all_notes_zip(
    auth_client: AsyncClient,
) -> None:
    """Test exporting all notes as ZIP file."""
    # Create two test notes
    note1_response = await auth_client.post(
        "/api/notes/",
        json={"title": "First Note", "content": "First content"},
    )
    assert note1_response.status_code == 201
    note1 = note1_response.json()

    note2_response = await auth_client.post(
        "/api/notes/",
        json={"title": "Second Note", "content": "Second content"},
    )
    assert note2_response.status_code == 201

    # Export as ZIP
    response = await auth_client.get("/api/notes/export/zip")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]

    # Verify ZIP contains markdown files
    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        namelist = zip_file.namelist()
        assert len(namelist) >= 2
        assert all(name.endswith(".md") for name in namelist)

        # Check content of first note
        for name in namelist:
            if note1["id"] in name:
                content = zip_file.read(name).decode("utf-8")
                assert "First Note" in content
                assert "First content" in content


@pytest.mark.asyncio
async def test_export_all_notes_zip_empty(
    auth_client: AsyncClient,
) -> None:
    """Test exporting when user has no notes returns 404."""
    # No notes created, so export should fail
    response = await auth_client.get("/api/notes/export/zip")
    assert response.status_code == 404
    assert response.json()["detail"] == "No notes found"
