from datetime import timedelta

from django.utils import timezone

from .email_service import send_campaign_email
from .models import ColdCampaign, ColdCampaignRecipient, ColdCampaignThreadMessage


STOP_REPLY_STATUSES = {
    ColdCampaignRecipient.REPLY_INTERESTED,
    ColdCampaignRecipient.REPLY_SCHEDULE,
    ColdCampaignRecipient.REPLY_UNSUBSCRIBE,
}


def schedule_initial_followups(campaign: ColdCampaign):
    """After bulk send completes for a recipient, schedule first follow-up."""
    if campaign.followup_count <= 0:
        return
    delays = campaign.followup_delay_days or []
    if not delays:
        delays = [3, 7, 14][: campaign.followup_count]
    first_delay = delays[0] if delays else 3
    when = timezone.now() + timedelta(days=int(first_delay))
    campaign.recipients.filter(
        status=ColdCampaignRecipient.STATUS_SENT,
        followup_step_sent=0,
        reply_status=ColdCampaignRecipient.REPLY_NONE,
    ).update(next_followup_at=when)


def _followup_subject_body(campaign: ColdCampaign, step: int) -> tuple[str, str]:
    subject = campaign.followup_subject_template or f'Re: {campaign.subject}'
    body = campaign.followup_body_html_template or campaign.body_html
    if step > 1:
        subject = f'Follow-up {step}: {subject}'
    return subject, body


def send_followup_for_recipient(recipient: ColdCampaignRecipient) -> bool:
    campaign = recipient.campaign
    if campaign.is_paused or campaign.status not in (
        ColdCampaign.STATUS_SENDING,
        ColdCampaign.STATUS_SENT,
    ):
        return False
    if recipient.reply_status in STOP_REPLY_STATUSES:
        recipient.next_followup_at = None
        recipient.save(update_fields=['next_followup_at'])
        return False
    if recipient.followup_step_sent >= campaign.followup_count:
        recipient.next_followup_at = None
        recipient.save(update_fields=['next_followup_at'])
        return False

    step = recipient.followup_step_sent + 1
    subject, body_html = _followup_subject_body(campaign, step)

    class _FollowupCampaign:
        def __init__(self, c, subj, html):
            self.subject = subj
            self.body_html = html
            self.body_text = c.body_text
            self.from_name = c.from_name
            self.from_email = c.from_email
            self.trial_url = c.trial_url

    proxy = _FollowupCampaign(campaign, subject, body_html)
    send_campaign_email(proxy, recipient, is_followup=True)

    ColdCampaignThreadMessage.objects.create(
        recipient=recipient,
        direction=ColdCampaignThreadMessage.DIRECTION_OUTBOUND,
        subject=subject[:500],
        body_text='',
        received_at=timezone.now(),
        classification=f'followup_{step}',
    )

    recipient.followup_step_sent = step
    delays = campaign.followup_delay_days or [3, 7, 14]
    if step < campaign.followup_count and step < len(delays):
        recipient.next_followup_at = timezone.now() + timedelta(days=int(delays[step]))
    else:
        recipient.next_followup_at = None
    recipient.save(update_fields=['followup_step_sent', 'next_followup_at'])
    return True


def process_due_followups():
    now = timezone.now()
    due = ColdCampaignRecipient.objects.filter(
        status=ColdCampaignRecipient.STATUS_SENT,
        next_followup_at__lte=now,
        campaign__is_paused=False,
    ).exclude(reply_status__in=STOP_REPLY_STATUSES).select_related('campaign')

    sent = 0
    for recipient in due:
        if send_followup_for_recipient(recipient):
            sent += 1
    return sent
