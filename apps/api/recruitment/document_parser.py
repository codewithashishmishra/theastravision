"""Local PDF/DOCX text extraction — no AI."""

from __future__ import annotations

import io
from pathlib import Path

from django.core.exceptions import ValidationError

ALLOWED_EXTENSIONS = {'.pdf', '.docx'}


def validate_upload_filename(filename: str) -> None:
    ext = Path((filename or '').lower()).suffix
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f'Only PDF and DOCX files are allowed. Got: {ext or "unknown"}'
        )


def parse_bytes(filename: str, content: bytes) -> str:
    validate_upload_filename(filename)
    name = filename.lower()
    if name.endswith('.pdf'):
        import fitz

        doc = fitz.open(stream=content, filetype='pdf')
        return '\n'.join(page.get_text() for page in doc).strip()
    if name.endswith('.docx'):
        from docx import Document

        doc = Document(io.BytesIO(content))
        return '\n'.join(p.text for p in doc.paragraphs if p.text).strip()
    raise ValidationError('Unsupported file type.')


def parse_uploaded_file(uploaded_file) -> str:
    if not uploaded_file:
        return ''
    name = uploaded_file.name or 'document.pdf'
    uploaded_file.seek(0)
    content = uploaded_file.read()
    return parse_bytes(name, content)
