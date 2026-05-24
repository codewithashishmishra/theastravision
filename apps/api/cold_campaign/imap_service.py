import email
import imaplib
from email.utils import parseaddr, parsedate_to_datetime

from django.utils import timezone

from core.models import EnvConfiguration

from .ai_service import classify_reply_snippet
from .models import (
    ColdCampaignImapState,
    ColdCampaignRecipient,
    ColdCampaignThreadMessage,
)


def get_imap_config() -> dict:
    return EnvConfiguration.get_cached_config('IMAP') or {}


def _reply_status_from_classification(classification: str) -> str:
    mapping = {
        'interested': ColdCampaignRecipient.REPLY_INTERESTED,
        'schedule': ColdCampaignRecipient.REPLY_SCHEDULE,
        'unsubscribe': ColdCampaignRecipient.REPLY_UNSUBSCRIBE,
        'replied': ColdCampaignRecipient.REPLY_REPLIED,
    }
    return mapping.get(classification, ColdCampaignRecipient.REPLY_OTHER)


def _find_recipient(from_email: str, in_reply_to: str, references: str):
    qs = ColdCampaignRecipient.objects.filter(
        status=ColdCampaignRecipient.STATUS_SENT,
        email__iexact=from_email,
    ).select_related('campaign')
    if in_reply_to:
        match = qs.filter(outbound_message_id__icontains=in_reply_to.strip('<> ')).first()
        if match:
            return match
    if references:
        for token in references.split():
            token = token.strip('<> ')
            match = qs.filter(outbound_message_id__icontains=token).first()
            if match:
                return match
    return qs.order_by('-sent_at').first()


def poll_inbound_replies():
    """Fetch new IMAP messages and attach to campaign recipient threads."""
    cfg = get_imap_config()
    host = cfg.get('host', '')
    if not host:
        return {'processed': 0, 'skipped': 'IMAP not configured'}

    port = int(cfg.get('port', 993))
    use_ssl = bool(cfg.get('use_ssl', True))
    user = cfg.get('user', '')
    password = cfg.get('password', '')
    folder = cfg.get('folder', 'INBOX')

    if use_ssl:
        conn = imaplib.IMAP4_SSL(host, port)
    else:
        conn = imaplib.IMAP4(host, port)
    conn.login(user, password)
    conn.select(folder)

    state, _ = ColdCampaignImapState.objects.get_or_create(mailbox_key='default')
    last_uid = int(state.last_uid) if state.last_uid.isdigit() else 0

    status, data = conn.uid('search', None, 'ALL')
    if status != 'OK':
        conn.logout()
        return {'processed': 0, 'error': 'search failed'}

    uids = [int(x) for x in data[0].split() if x] if data[0] else []
    new_uids = [u for u in uids if u > last_uid]
    processed = 0
    max_uid = last_uid

    for uid in new_uids:
        max_uid = max(max_uid, uid)
        uid_key = str(uid)
        if ColdCampaignThreadMessage.objects.filter(imap_uid=uid_key, direction=ColdCampaignThreadMessage.DIRECTION_INBOUND).exists():
            continue

        status, msg_data = conn.uid('fetch', str(uid).encode(), '(RFC822)')
        if status != 'OK' or not msg_data or not msg_data[0]:
            continue

        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        from_addr = parseaddr(msg.get('From', ''))[1]
        subject = msg.get('Subject', '') or ''
        in_reply_to = msg.get('In-Reply-To', '') or ''
        references = msg.get('References', '') or ''

        body_text = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode(errors='replace')
                    break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body_text = payload.decode(errors='replace')

        try:
            received_at = parsedate_to_datetime(msg.get('Date', ''))
            if timezone.is_naive(received_at):
                received_at = timezone.make_aware(received_at)
        except (TypeError, ValueError):
            received_at = timezone.now()

        recipient = _find_recipient(from_addr, in_reply_to, references)
        if not recipient:
            continue

        classification = classify_reply_snippet(body_text[:2000])
        reply_status = _reply_status_from_classification(classification)

        ColdCampaignThreadMessage.objects.create(
            recipient=recipient,
            direction=ColdCampaignThreadMessage.DIRECTION_INBOUND,
            subject=subject[:500],
            body_text=body_text[:10000],
            received_at=received_at,
            imap_uid=uid_key,
            classification=classification,
        )

        recipient.reply_status = reply_status
        recipient.last_reply_at = received_at
        recipient.last_reply_snippet = body_text[:500]
        if reply_status in (
            ColdCampaignRecipient.REPLY_INTERESTED,
            ColdCampaignRecipient.REPLY_SCHEDULE,
            ColdCampaignRecipient.REPLY_UNSUBSCRIBE,
            ColdCampaignRecipient.REPLY_REPLIED,
        ):
            recipient.next_followup_at = None
        recipient.save(
            update_fields=[
                'reply_status',
                'last_reply_at',
                'last_reply_snippet',
                'next_followup_at',
            ]
        )
        processed += 1

        try:
            from notifications.services import notify_user

            campaign = recipient.campaign
            creator = campaign.created_by
            tenant_id = getattr(creator, 'tenant_id', None) if creator else None
            if creator and tenant_id:
                notify_user(
                    str(creator.id),
                    str(tenant_id),
                    f'Cold email reply: {recipient.email}',
                    f'{classification}: {subject[:120]}',
                )
        except Exception:
            pass

    state.last_uid = str(max_uid)
    state.save(update_fields=['last_uid', 'updated_at'])
    conn.logout()
    return {'processed': processed, 'last_uid': max_uid}
