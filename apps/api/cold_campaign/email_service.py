from django.conf import settings

from core.email.smtp_client import (
    TRACKING_GIF_BYTES,
    build_smtp_connection,
    get_platform_smtp_config,
    get_public_api_base_url,
)
from core.models import EnvConfiguration

from .copy_templates import apply_merge_tags, html_to_plain


def get_smtp_config() -> dict:
    return get_platform_smtp_config()


def tracking_pixel_html(tracking_token) -> str:
    url = f'{get_public_api_base_url()}/api/v1/cold-campaigns/track/{tracking_token}.gif'
    return (
        f'<img src="{url}" width="1" height="1" alt="" '
        f'style="display:block;width:1px;height:1px;border:0;opacity:0;" />'
    )


def inject_tracking_pixel(html: str, tracking_token) -> str:
    pixel = tracking_pixel_html(tracking_token)
    lower = html.lower()
    if '</body>' in lower:
        idx = lower.rfind('</body>')
        return html[:idx] + pixel + html[idx:]
    return html + pixel


def render_campaign_email(
    campaign,
    recipient,
    *,
    include_tracking: bool = True,
) -> tuple[str, str, str]:
    trial_url = campaign.trial_url or 'mailto:sales@theastravision.com?subject=AastraaHR%203-day%20trial%20request'
    subject = apply_merge_tags(
        campaign.subject,
        first_name=recipient.first_name,
        company=recipient.company,
        trial_url=trial_url,
    )
    body_html = apply_merge_tags(
        campaign.body_html,
        first_name=recipient.first_name,
        company=recipient.company,
        trial_url=trial_url,
    )
    if include_tracking:
        body_html = inject_tracking_pixel(body_html, recipient.tracking_token)
    body_text = campaign.body_text or html_to_plain(body_html)
    body_text = apply_merge_tags(
        body_text,
        first_name=recipient.first_name,
        company=recipient.company,
        trial_url=trial_url,
    )
    return subject, body_html, body_text


def send_campaign_email(
    campaign,
    recipient,
    *,
    connection=None,
    include_tracking: bool = True,
    is_followup: bool = False,
) -> None:
    from core.email.outbound import send_tenant_email
    from core.email.utils import resolve_platform_tenant_id
    from .models import ColdCampaignThreadMessage

    tenant_id = resolve_platform_tenant_id(campaign)
    if not tenant_id:
        raise ValueError('No tenant available for outbound email logging.')

    if hasattr(recipient, 'ensure_outbound_message_id'):
        msg_id = recipient.ensure_outbound_message_id()
        if not recipient.outbound_message_id:
            recipient.save(update_fields=['outbound_message_id'])
    else:
        msg_id = None

    subject, body_html, body_text = render_campaign_email(
        campaign, recipient, include_tracking=include_tracking and not is_followup
    )
    extra_headers = {'Message-ID': msg_id} if msg_id else None
    if connection:
        # Legacy batch path: still log via hub without reusing external connection
        pass
    send_tenant_email(
        tenant_id=tenant_id,
        to=recipient.email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        source='cold_campaign',
        source_id=str(campaign.id),
        track_opens=False,
        extra_headers=extra_headers,
    )

    if getattr(recipient, 'pk', None):
        from django.utils import timezone

        ColdCampaignThreadMessage.objects.create(
            recipient=recipient,
            direction=ColdCampaignThreadMessage.DIRECTION_OUTBOUND,
            subject=subject[:500],
            body_text=body_text[:5000],
            received_at=timezone.now(),
            classification='followup' if is_followup else 'initial',
        )
