"""Utilities for career portal and job board."""

from __future__ import annotations

import re

import bleach
from django.utils.text import slugify

ALLOWED_HTML_TAGS = [
    'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'a', 'blockquote'
]
ALLOWED_HTML_ATTRS = {'a': ['href', 'title', 'target', 'rel']}


def sanitize_job_html(html: str) -> str:
    if not html:
        return ''
    return bleach.clean(
        html,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRS,
        strip=True,
    )


def unique_job_slug(tenant_id, title: str, exclude_id=None) -> str:
    from recruitment.models import JobRequisition

    base = slugify(title)[:200] or 'job'
    candidate = base
    n = 1
    qs = JobRequisition.objects.filter(tenant_id=tenant_id, slug=candidate)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    while qs.exists():
        n += 1
        candidate = f'{base}-{n}'
        qs = JobRequisition.objects.filter(tenant_id=tenant_id, slug=candidate)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
    return candidate


def job_description_html(job) -> str:
    if job.rich_description_html:
        return sanitize_job_html(job.rich_description_html)
    text = job.description or ''
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        return ''
    return ''.join(f'<p>{bleach.clean(p)}</p>' for p in paragraphs)
