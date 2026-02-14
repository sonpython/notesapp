"""Note export service -- converts notes to markdown and PDF formats."""

from __future__ import annotations

import markdown
from weasyprint import HTML

from app.models.note import Note


def export_note_as_markdown(note: Note) -> str:
    """
    Export a note as plain markdown text.

    Format:
    # {title}

    {content}

    ---
    Created: {created_at}
    Updated: {updated_at}
    """
    title = note.title or "Untitled"
    content = note.content or ""
    created = note.created_at.strftime("%Y-%m-%d %H:%M:%S")
    updated = note.updated_at.strftime("%Y-%m-%d %H:%M:%S")

    return f"""# {title}

{content}

---
Created: {created}
Updated: {updated}
"""


def export_note_as_pdf(note: Note) -> bytes:
    """
    Export a note as PDF by converting markdown to HTML then to PDF.

    Uses weasyprint for PDF generation with basic styling.
    """
    markdown_text = export_note_as_markdown(note)

    # Convert markdown to HTML
    html_content = markdown.markdown(
        markdown_text,
        extensions=["fenced_code", "tables", "nl2br"],
    )

    # Wrap in styled HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 0.3em;
            }}
            h2, h3, h4, h5, h6 {{
                color: #34495e;
                margin-top: 1.5em;
            }}
            code {{
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: "Courier New", monospace;
            }}
            pre {{
                background: #f4f4f4;
                padding: 1em;
                border-radius: 5px;
                overflow-x: auto;
            }}
            pre code {{
                background: none;
                padding: 0;
            }}
            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 1em;
                color: #555;
                margin: 1em 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px 12px;
                text-align: left;
            }}
            th {{
                background: #3498db;
                color: white;
            }}
            hr {{
                border: none;
                border-top: 1px solid #ddd;
                margin: 2em 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Generate PDF
    pdf = HTML(string=full_html).write_pdf()
    return pdf
