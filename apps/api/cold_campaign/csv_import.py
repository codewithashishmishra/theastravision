import csv
import io
import re

from django.core.validators import validate_email
from django.core.exceptions import ValidationError


EMAIL_RE = re.compile(r'^[^@]+@[^@]+\.[^@]+$')


def parse_recipients_csv(file_obj) -> tuple[list[dict], list[str]]:
    """
    Parse CSV with headers: email (required), first_name, company.
    Returns (rows, errors).
    """
    raw = file_obj.read()
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8-sig', errors='replace')
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        return [], ['CSV is empty or missing a header row.']

    normalized = {h.strip().lower().replace(' ', '_'): h for h in reader.fieldnames if h}
    if 'email' not in normalized:
        return [], ['CSV must include an "email" column.']

    rows = []
    errors = []
    seen = set()

    for line_no, row in enumerate(reader, start=2):
        email = (row.get(normalized['email']) or '').strip().lower()
        if not email:
            continue
        if email in seen:
            errors.append(f'Line {line_no}: duplicate email skipped ({email}).')
            continue
        try:
            validate_email(email)
        except ValidationError:
            if not EMAIL_RE.match(email):
                errors.append(f'Line {line_no}: invalid email ({email}).')
                continue
        seen.add(email)
        first_name = ''
        company = ''
        if 'first_name' in normalized:
            first_name = (row.get(normalized['first_name']) or '').strip()
        if 'company' in normalized:
            company = (row.get(normalized['company']) or '').strip()
        rows.append({'email': email, 'first_name': first_name, 'company': company})

    if not rows and not errors:
        errors.append('No valid recipient rows found.')
    return rows, errors
