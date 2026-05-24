"""Fill official government PDF templates or fall back to structured PDF generation."""

from __future__ import annotations

import io
import json
from pathlib import Path

import fitz
from pypdf import PdfReader, PdfWriter

from compliance.dynamic_field_map import (
    build_acroform_values,
    load_or_resolve_field_map,
    list_acroform_field_names,
)

COMPLIANCE_ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = COMPLIANCE_ROOT / 'data' / 'form_registry.json'


def load_form_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))


def get_registry_entry(jurisdiction: str, doc_type: str, tax_year: int) -> dict | None:
    for entry in load_form_registry():
        if entry['jurisdiction'] == jurisdiction and entry['doc_type'] == doc_type and entry['tax_year'] == tax_year:
            return entry
    for entry in load_form_registry():
        if entry['jurisdiction'] == jurisdiction and entry['doc_type'] == doc_type:
            return entry
    return None


def template_path(entry: dict) -> Path:
    return COMPLIANCE_ROOT / entry.get('template_path', '')


def pdf_from_text(title: str, lines: list[str]) -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    y = 50
    page.insert_text((50, y), title, fontsize=16)
    y += 30
    for line in lines:
        if y > 800:
            page = doc.new_page(width=595, height=842)
            y = 50
        page.insert_text((50, y), line, fontsize=10)
        y += 14
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def fill_government_pdf(
    jurisdiction: str,
    doc_type: str,
    tax_year: int,
    data: dict[str, str],
    fallback_lines: list[str],
    fallback_title: str,
) -> tuple[bytes, dict]:
    """Return (pdf_bytes, metadata) with fill_strategy used."""
    entry = get_registry_entry(jurisdiction, doc_type, tax_year)
    meta: dict = {'fill_strategy': 'html_fallback', 'doc_type': doc_type, 'tax_year': tax_year}

    if not entry:
        meta['note'] = 'No registry entry'
        return pdf_from_text(fallback_title, fallback_lines), meta

    template = template_path(entry)
    meta['source_url'] = entry.get('source_url', '')

    if not template.exists():
        meta['note'] = f'Template missing: {template.name}. Run download_form_templates.'
        return pdf_from_text(fallback_title, fallback_lines), meta

    field_map_config = load_or_resolve_field_map(entry, template)
    pdf_fields = field_map_config.get('fields', {})
    meta['dynamic'] = field_map_config.get('dynamic', False)
    meta['auto_resolved'] = field_map_config.get('auto_resolved', False)

    if not pdf_fields:
        available = list_acroform_field_names(template)
        meta['note'] = f'No fields resolved ({len(available)} AcroForm fields in template)'
        return pdf_from_text(fallback_title, fallback_lines), meta

    acro_values = build_acroform_values(doc_type, pdf_fields, data)

    # Drop values whose PDF field no longer exists (template year changed)
    available = set(list_acroform_field_names(template))
    if available:
        acro_values = {k: v for k, v in acro_values.items() if k in available}

    if not acro_values:
        meta['fill_strategy'] = 'html_fallback'
        meta['note'] = 'No AcroForm values after dynamic mapping'
        meta['resolved_fields'] = list(pdf_fields.keys())
        return pdf_from_text(fallback_title, fallback_lines), meta

    try:
        reader = PdfReader(str(template))
        writer = PdfWriter()
        writer.append(reader)
        for page in writer.pages:
            writer.update_page_form_field_values(page, acro_values, auto_regenerate=False)
        out = io.BytesIO()
        writer.write(out)
        meta['fill_strategy'] = 'acroform'
        meta['fields_filled'] = list(acro_values.keys())
        meta['logical_keys'] = list(data.keys())
        return out.getvalue(), meta
    except Exception as exc:
        meta['fill_strategy'] = 'html_fallback'
        meta['error'] = str(exc)
        return pdf_from_text(fallback_title, fallback_lines), meta
