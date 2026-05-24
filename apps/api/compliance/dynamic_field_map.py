"""Discover AcroForm field names from government PDFs and map logical payroll keys."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

COMPLIANCE_ROOT = Path(__file__).resolve().parent


@dataclass
class FieldRule:
    logical_key: str
    patterns: tuple[str, ...]
    """Glob-style patterns matched against full AcroForm field paths."""


# Per-form rules: patterns match IRS/CRA semantic segments in field paths (year-agnostic).
FORM_FIELD_RULES: dict[str, dict] = {
    'W2': {
        'copy_preference': ('Copy1', 'CopyA', 'Copy2', 'CopyB'),
        'rules': [
            FieldRule('employer_name', ('*Col_Left*.f2_02[0]', '*Employer*.f1_1[0]')),
            FieldRule('employer_ein', ('*Col_Left*.f2_03[0]', '*Employer*.f1_2[0]')),
            FieldRule('employee_ssn', ('*Col_Left*.f2_04[0]', '*Employee*.f1_3[0]')),
            FieldRule('employee_first_name', ('*FirstName_ReadOrder*.f2_05[0]', '*EmployeeName*.f1_1[0]')),
            FieldRule('employee_last_name', ('*LastName_ReadOrder*.f2_06[0]', '*EmployeeName*.f1_3[0]')),
            FieldRule('box1_wages', ('*Box1_ReadOrder*.f2_*[0]',)),
            FieldRule('box2_federal_tax', ('*Col_Right*.f2_10[0]', '*Box2_ReadOrder*.f2_*[0]')),
            FieldRule('box3_ss_wages', ('*Box3_ReadOrder*.f2_*[0]',)),
            FieldRule('box4_ss_tax', ('*Col_Right*.f2_12[0]', '*Box4_ReadOrder*.f2_*[0]')),
            FieldRule('box5_medicare_wages', ('*Box5_ReadOrder*.f2_*[0]',)),
            FieldRule('box6_medicare_tax', ('*Col_Right*.f2_14[0]', '*Box6_ReadOrder*.f2_*[0]')),
        ],
        'data_aliases': {
            'box1_wages': ('box1_wages',),
            'box2_federal_tax': ('box2_federal_tax',),
            'box4_ss_tax': ('box4_ss_tax',),
            'box6_medicare_tax': ('box6_medicare_tax',),
        },
    },
    'FORM1095C': {
        'copy_preference': ('Page1',),
        'rules': [
            FieldRule('employer_name', ('*EmployerIssuer*.f1_9[0]', '*EmployerIssuer*.f1_10[0]')),
            FieldRule('employer_ein', ('*EmployerIssuer*.f1_11[0]', '*EmployerIssuer*.f1_12[0]')),
            FieldRule('employee_first_name', ('*EmployeeName*.f1_1[0]',)),
            FieldRule('employee_last_name', ('*EmployeeName*.f1_3[0]',)),
            FieldRule('employee_ssn', ('*EmployeeName*.f1_2[0]', '*EmployeeName*.f1_4[0]')),
            FieldRule('offer_of_coverage', ('*PartII*.f1_16[0]', '*Table1*.Row1*.f1_18[0]')),
        ],
        'data_aliases': {
            'offer_of_coverage': ('offer_of_coverage',),
        },
    },
    'T4': {
        'copy_preference': (),
        'rules': [
            FieldRule('employer_name', ('*Employer*.f1_1[0]', '*box14*', '*Box14*')),
            FieldRule('employee_name', ('*Employee*.f1_2[0]', '*LastName*')),
            FieldRule('box14_income', ('*Box14*.f1_*[0]', '*box14*.f1_*[0]')),
            FieldRule('box16_cpp', ('*Box16*.f1_*[0]', '*box16*.f1_*[0]')),
            FieldRule('box18_ei', ('*Box18*.f1_*[0]', '*box18*.f1_*[0]')),
            FieldRule('box22_tax', ('*Box22*.f1_*[0]', '*box22*.f1_*[0]')),
        ],
        'data_aliases': {},
    },
    'RL1': {
        'copy_preference': (),
        'rules': [
            FieldRule('employee_name', ('*Employee*.f1_*[0]', '*Nom*')),
            FieldRule('income', ('*Revenu*.f1_*[0]', '*Income*.f1_*[0]')),
        ],
        'data_aliases': {},
    },
    'FORM16': {
        'copy_preference': (),
        'rules': [
            FieldRule('employer_name', ('*Employer*', '*Deductor*')),
            FieldRule('employee_name', ('*Employee*', '*Assessee*')),
            FieldRule('pan', ('*PAN*', '*pan*')),
            FieldRule('gross_salary', ('*Gross*', '*Salary*')),
            FieldRule('tds_deducted', ('*TDS*', '*Tax*')),
        ],
        'data_aliases': {},
    },
    'FORM12BA': {
        'copy_preference': (),
        'rules': [
            FieldRule('employee_name', ('*Employee*', '*Name*')),
            FieldRule('employer_name', ('*Employer*',)),
        ],
        'data_aliases': {},
    },
}


def list_acroform_field_names(template: Path) -> list[str]:
    try:
        reader = PdfReader(str(template))
        return sorted((reader.get_fields() or {}).keys())
    except Exception:
        return []


def _filter_by_copy(names: list[str], copy_preference: tuple[str, ...]) -> list[str]:
    if not copy_preference:
        return names
    for copy in copy_preference:
        subset = [n for n in names if f'.{copy}[' in n or f'.{copy}.' in n]
        if subset:
            return subset
    return names


def _pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """Glob with only `*` wildcard; literal `[` `]` so AcroForm indices match."""
    parts = []
    for ch in pattern:
        if ch == '*':
            parts.append('.*')
        else:
            parts.append(re.escape(ch))
    return re.compile('^' + ''.join(parts) + '$')


def _first_match(names: list[str], pattern: str) -> str | None:
    rx = _pattern_to_regex(pattern)
    for name in names:
        if rx.search(name):
            return name
    return None


def resolve_fields_for_form(doc_type: str, template: Path) -> dict[str, str]:
    """Build logical_key -> full AcroForm path from template structure."""
    spec = FORM_FIELD_RULES.get(doc_type)
    if not spec:
        return {}

    all_names = list_acroform_field_names(template)
    if not all_names:
        return {}

    scoped = _filter_by_copy(all_names, spec.get('copy_preference', ()))
    resolved: dict[str, str] = {}
    used: set[str] = set()

    for rule in spec.get('rules', []):
        for pattern in rule.patterns:
            match = _first_match(scoped, pattern)
            if match and match not in used:
                resolved[rule.logical_key] = match
                used.add(match)
                break

    # W-2: fill box fields by Box{N}_ReadOrder when rules missed
    if doc_type == 'W2':
        _resolve_w2_box_fallback(scoped, resolved, used)

    return resolved


def _resolve_w2_box_fallback(scoped: list[str], resolved: dict[str, str], used: set[str]) -> None:
    box_map = {
        1: 'box1_wages',
        2: 'box2_federal_tax',
        3: 'box3_ss_wages',
        4: 'box4_ss_tax',
        5: 'box5_medicare_wages',
        6: 'box6_medicare_tax',
    }
    for box_num, logical in box_map.items():
        if logical in resolved:
            continue
        pattern = f'*Box{box_num}_ReadOrder*.f2_*[0]'
        match = _first_match(scoped, pattern)
        if match and match not in used:
            resolved[logical] = match
            used.add(match)
            continue
        # Amount fields between read-order groups (IRS fw2 layout)
        fallbacks = {
            2: '*Col_Right*.f2_10[0]',
            4: '*Col_Right*.f2_12[0]',
            6: '*Col_Right*.f2_14[0]',
        }
        if box_num in fallbacks:
            match = _first_match(scoped, fallbacks[box_num])
            if match and match not in used:
                resolved[logical] = match
                used.add(match)


def expand_data_for_form(doc_type: str, data: dict[str, str]) -> dict[str, str]:
    """Map service-layer keys to logical keys used by dynamic resolver."""
    expanded = dict(data)
    if doc_type == 'W2':
        if 'employee_name' in data and 'employee_first_name' not in data:
            parts = data['employee_name'].split(None, 1)
            expanded['employee_first_name'] = parts[0] if parts else ''
            expanded['employee_last_name'] = parts[1] if len(parts) > 1 else ''
    return expanded


def build_acroform_values(
    doc_type: str,
    field_map: dict[str, str],
    data: dict[str, str],
) -> dict[str, str]:
    expanded = expand_data_for_form(doc_type, data)
    spec = FORM_FIELD_RULES.get(doc_type, {})
    aliases = spec.get('data_aliases', {})

    acro: dict[str, str] = {}
    for logical_key, pdf_field in field_map.items():
        value = expanded.get(logical_key)
        if value is None and logical_key in aliases:
            for alt in aliases[logical_key]:
                if alt in expanded:
                    value = expanded[alt]
                    break
        if value is not None and str(value) != '':
            acro[pdf_field] = str(value)
    return acro


def load_or_resolve_field_map(entry: dict, template: Path) -> dict:
    """
    Return field map config with resolved `fields` dict.
    Uses JSON cache keyed by template mtime when `dynamic: true`.
    """
    rel = entry.get('field_map_path', '')
    cache_path = COMPLIANCE_ROOT / rel if rel else None
    doc_type = entry['doc_type']
    template_mtime = template.stat().st_mtime if template.exists() else 0

    static: dict = {'fields': {}, 'overlay_fallback': True, 'dynamic': True}
    if cache_path and cache_path.exists():
        try:
            static = json.loads(cache_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            pass

    use_dynamic = static.get('dynamic', True) or not static.get('fields')

    if not use_dynamic and static.get('fields'):
        return static

    resolved = resolve_fields_for_form(doc_type, template)
    if resolved:
        cached = {
            'dynamic': True,
            'auto_resolved': True,
            'template_mtime': template_mtime,
            'template_path': entry.get('template_path', ''),
            'fields': resolved,
            'overlay_fallback': static.get('overlay_fallback', True),
        }
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cached, indent=2), encoding='utf-8')
        return cached

    return static


def suggest_field_map_json(doc_type: str, template: Path) -> str:
    """Pretty JSON for inspect_form_fields command output."""
    resolved = resolve_fields_for_form(doc_type, template)
    payload = {
        'dynamic': True,
        'auto_resolved': True,
        'fields': resolved,
        'overlay_fallback': True,
    }
    return json.dumps(payload, indent=2)
