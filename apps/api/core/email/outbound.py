"""Central outbound email hub with logging and open tracking."""

from __future__ import annotations

import logging
import re

from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from core.email.sender import resolve_sender
from core.email.smtp_client import TRACKING_GIF_BYTES, build_smtp_connection, get_public_api_base_url
from core.models import OutboundEmailLog, TenantEmailSettings

logger = logging.getLogger(__name__)

BODY_TRUNCATE = 50000


def _truncate(text: str, limit: int = BODY_TRUNCATE) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + '...'


def _inject_tracking_pixel(html: str, log_id) -> str:
    base = get_public_api_base_url()
    pixel = f'<img src="{base}/api/v1/email/track/{log_id}.gif" width="1" height="1" alt="" style="display:none" />'
    if '</body>' in html.lower():
        return re.sub(r'</body>', pixel + '</body>', html, count=1, flags=re.IGNORECASE)
    return html + pixel


def notify_tenant_admins_for_email(tenant_id, log: OutboundEmailLog, *, event: str) -> None:
    from notifications.services import notify_user

    try:
        try:
            settings_obj = TenantEmailSettings.objects.get(tenant_id=tenant_id)
            roles = settings_obj.notify_roles or ['Company Admin', 'HR Admin']
        except TenantEmailSettings.DoesNotExist:
            roles = ['Company Admin', 'HR Admin']

        from core.models import UserRoleMapping

        user_ids = (
            UserRoleMapping.objects.filter(
                user__tenant_id=tenant_id,
                role__tenant_id=tenant_id,
                role__name__in=roles,
            )
            .values_list('user_id', flat=True)
            .distinct()
        )
        to_display = ', '.join(log.to_emails[:3])
        if len(log.to_emails) > 3:
            to_display += f' (+{len(log.to_emails) - 3})'

        if event == 'sent':
            title = f'Email sent to {to_display}'
            category = 'email_sent'
        elif event == 'failed':
            title = f'Email failed: {to_display}'
            category = 'email_failed'
        else:
            title = f'Email opened: {log.subject[:80]}'
            category = 'email_opened'

        link = f'/hr/email-logs?log={log.id}'
        for uid in user_ids:
            notify_user(
                uid,
                tenant_id,
                title,
                log.subject,
                category=category,
                link=link,
                email_log_id=log.id,
            )
    except Exception:
        logger.warning(
            'notify_tenant_admins_for_email failed log=%s event=%s',
            log.id,
            event,
            exc_info=True,
        )


def send_tenant_email(
    *,
    tenant_id,
    to,
    subject: str,
    body_html: str,
    body_text: str = '',
    source: str = 'general',
    source_id: str | None = None,
    created_by=None,
    cc=None,
    parent_log=None,
    track_opens: bool = True,
    extra_headers: dict | None = None,
) -> OutboundEmailLog:
    if isinstance(to, str):
        to_list = [to]
    else:
        to_list = list(to)
    cc_list = list(cc or [])

    from_email, from_name, reply_to, _ = resolve_sender(tenant_id)
    log = OutboundEmailLog.objects.create(
        tenant_id=tenant_id,
        from_email=from_email,
        from_name=from_name,
        to_emails=to_list,
        cc_emails=cc_list,
        subject=subject[:500],
        body_html=_truncate(body_html),
        body_text=_truncate(body_text or ''),
        status=OutboundEmailLog.STATUS_QUEUED,
        source=source,
        source_id=source_id or '',
        created_by=created_by,
        parent_log=parent_log,
    )

    html = body_html
    if track_opens and html:
        html = _inject_tracking_pixel(html, log.id)

    try:
        conn = build_smtp_connection()
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body_text or 'View this message in HTML format.',
            from_email=f'{from_name} <{from_email}>',
            to=to_list,
            cc=cc_list or None,
            reply_to=[reply_to] if reply_to else None,
            connection=conn,
        )
        if html:
            msg.attach_alternative(html, 'text/html')
        if extra_headers:
            for key, value in extra_headers.items():
                if value:
                    msg.extra_headers[key] = value
        msg.send()
        log.status = OutboundEmailLog.STATUS_SENT
        log.sent_at = timezone.now()
        log.message_id = getattr(msg, 'extra_headers', {}).get('Message-ID', '') or ''
        log.save(update_fields=['status', 'sent_at', 'message_id', 'updated_at'])
        notify_tenant_admins_for_email(tenant_id, log, event='sent')
    except Exception as exc:
        logger.exception('send_tenant_email failed log=%s', log.id)
        log.status = OutboundEmailLog.STATUS_FAILED
        log.smtp_error = str(exc)[:2000]
        log.save(update_fields=['status', 'smtp_error', 'updated_at'])
        notify_tenant_admins_for_email(tenant_id, log, event='failed')
    return log


def mark_email_opened(log_id) -> OutboundEmailLog | None:
    try:
        log = OutboundEmailLog.objects.get(pk=log_id)
    except OutboundEmailLog.DoesNotExist:
        return None
    if log.opened_at:
        return log
    log.opened_at = timezone.now()
    if log.status == OutboundEmailLog.STATUS_SENT:
        log.status = OutboundEmailLog.STATUS_OPENED
    log.save(update_fields=['opened_at', 'status', 'updated_at'])
    notify_tenant_admins_for_email(log.tenant_id, log, event='opened')
    return log
