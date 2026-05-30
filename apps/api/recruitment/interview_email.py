"""Formatting and context for interview invite emails."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_datetime


def _resolve_tz_name(session) -> str:
    flags = session.proctor_flags or {}
    if flags.get('scheduled_timezone'):
        return str(flags['scheduled_timezone'])
    tenant = getattr(session.candidate, 'tenant', None) or getattr(session.job, 'tenant', None)
    if tenant and getattr(tenant, 'timezone', None):
        return tenant.timezone
    return 'Asia/Kolkata'


def format_interview_datetime(value, tz_name: str) -> str:
    if not value:
        return ''
    if isinstance(value, str):
        dt = parse_datetime(value)
    else:
        dt = value
    if not dt:
        return str(value)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo('UTC')
    local = dt.astimezone(tz)
    abbrev = local.strftime('%Z') or tz_name
    return local.strftime('%d %b %Y, %I:%M %p').lstrip('0').replace(' 0', ' ') + f' {abbrev}'


def build_invite_email_context(session) -> dict:
    candidate = session.candidate
    job = session.job
    flags = session.proctor_flags or {}
    tz_name = _resolve_tz_name(session)
    tenant = getattr(candidate, 'tenant', None) or getattr(job, 'tenant', None)
    company = getattr(tenant, 'name', None) or 'AastraaHR'

    scheduled_display = ''
    if flags.get('scheduled_at'):
        scheduled_display = format_interview_datetime(flags['scheduled_at'], tz_name)

    expiry_display = ''
    if session.expires_at:
        expiry_display = format_interview_datetime(session.expires_at, tz_name)

    from recruitment.email_service import get_frontend_base_url

    link = f"{get_frontend_base_url()}/interview/join/{session.magic_token}"
    reply_to = (flags.get('cc_emails') or [None])[0]

    return {
        'candidate_first_name': candidate.first_name,
        'job_title': job.title,
        'company_name': company,
        'interview_link': link,
        'scheduled_display': scheduled_display,
        'expiry_display': expiry_display,
        'has_expiry': bool(expiry_display),
        'reply_to': reply_to,
    }


def render_invite_email(session) -> tuple[str, str, str]:
    ctx = build_invite_email_context(session)
    subject = f"Interview invitation — {ctx['job_title']} at {ctx['company_name']}"
    body_html = render_to_string('recruitment/interview_invite_email.html', ctx)
    body_text = render_to_string('recruitment/interview_invite_email.txt', ctx)
    return subject, body_html, body_text
