import time

from celery import shared_task
from django.utils import timezone

from core.models import EnvConfiguration

from .email_service import build_smtp_connection, send_campaign_email
from .followup_service import schedule_initial_followups
from .imap_service import poll_inbound_replies
from .models import ColdCampaign, ColdCampaignRecipient


def _rate_per_minute() -> int:
    cfg = EnvConfiguration.get_cached_config('SMTP') or {}
    return max(1, int(cfg.get('rate_per_minute', 30)))


@shared_task
def send_campaign_batch(campaign_id: str, recipient_ids: list[str]):
    try:
        campaign = ColdCampaign.objects.get(pk=campaign_id)
    except ColdCampaign.DoesNotExist:
        return

    if campaign.is_paused:
        return

    delay = 60.0 / _rate_per_minute()
    conn = build_smtp_connection()

    try:
        for rid in recipient_ids:
            campaign.refresh_from_db(fields=['is_paused', 'status'])
            if campaign.is_paused:
                break

            try:
                recipient = ColdCampaignRecipient.objects.get(
                    pk=rid, campaign=campaign, status=ColdCampaignRecipient.STATUS_PENDING
                )
            except ColdCampaignRecipient.DoesNotExist:
                continue
            try:
                recipient.ensure_outbound_message_id()
                send_campaign_email(campaign, recipient, connection=conn)
                recipient.status = ColdCampaignRecipient.STATUS_SENT
                recipient.sent_at = timezone.now()
                recipient.error_message = ''
                recipient.save(
                    update_fields=[
                        'status',
                        'sent_at',
                        'error_message',
                        'outbound_message_id',
                    ]
                )
            except Exception as exc:
                recipient.status = ColdCampaignRecipient.STATUS_FAILED
                recipient.error_message = str(exc)[:2000]
                recipient.save(update_fields=['status', 'error_message'])
            time.sleep(delay)
    finally:
        conn.close()

    _finalize_campaign_status(campaign_id)


def _finalize_campaign_status(campaign_id: str):
    campaign = ColdCampaign.objects.get(pk=campaign_id)
    if campaign.is_paused:
        return
    pending = campaign.recipients.filter(status=ColdCampaignRecipient.STATUS_PENDING).exists()
    if pending:
        return
    sending = campaign.recipients.filter(status=ColdCampaignRecipient.STATUS_SENT).exists()
    failed_only = campaign.failed_count > 0 and campaign.sent_count == 0
    if failed_only:
        campaign.status = ColdCampaign.STATUS_FAILED
    else:
        campaign.status = ColdCampaign.STATUS_SENT
        schedule_initial_followups(campaign)
    campaign.save(update_fields=['status', 'updated_at'])


@shared_task
def dispatch_campaign_send(campaign_id: str):
    campaign = ColdCampaign.objects.get(pk=campaign_id)
    campaign.is_paused = False
    campaign.save(update_fields=['is_paused', 'updated_at'])
    pending_ids = [
        str(x)
        for x in campaign.recipients.filter(
            status=ColdCampaignRecipient.STATUS_PENDING
        ).values_list('id', flat=True)
    ]
    if not pending_ids:
        campaign.status = ColdCampaign.STATUS_SENT
        campaign.save(update_fields=['status', 'updated_at'])
        return
    send_campaign_batch.delay(str(campaign_id), pending_ids)


@shared_task
def resume_campaign_send(campaign_id: str):
    campaign = ColdCampaign.objects.get(pk=campaign_id)
    if campaign.status != ColdCampaign.STATUS_SENDING:
        return
    campaign.is_paused = False
    campaign.save(update_fields=['is_paused', 'updated_at'])
    pending_ids = [
        str(x)
        for x in campaign.recipients.filter(
            status=ColdCampaignRecipient.STATUS_PENDING
        ).values_list('id', flat=True)
    ]
    if pending_ids:
        send_campaign_batch.delay(str(campaign_id), pending_ids)


@shared_task
def process_cold_campaign_followups():
    from .followup_service import process_due_followups

    return process_due_followups()


@shared_task
def poll_cold_campaign_replies():
    return poll_inbound_replies()
