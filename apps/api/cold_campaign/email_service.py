from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

from core.models import EnvConfiguration

from .copy_templates import apply_merge_tags, html_to_plain


def get_smtp_config() -> dict:
    return EnvConfiguration.get_cached_config('SMTP') or {}


def get_public_api_base_url() -> str:
    return getattr(settings, 'PUBLIC_API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')


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


def build_smtp_connection():
    cfg = get_smtp_config()
    host = cfg.get('host', '')
    if not host:
        raise ValueError('SMTP is not configured. Save SMTP settings under Platform Config.')
    port = int(cfg.get('port', 587))
    use_tls = bool(cfg.get('use_tls', True))
    use_ssl = bool(cfg.get('use_ssl', False))
    user = cfg.get('user', '')
    password = cfg.get('password', '')
    return get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=host,
        port=port,
        username=user or None,
        password=password or None,
        use_tls=use_tls,
        use_ssl=use_ssl,
        fail_silently=False,
    )


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


def send_campaign_email(campaign, recipient, *, connection=None, include_tracking: bool = True) -> None:
    cfg = get_smtp_config()
    from_email = campaign.from_email or cfg.get('from_email') or cfg.get('user', '')
    from_name = campaign.from_name or cfg.get('from_name', 'The Astra Vision')
    if not from_email:
        raise ValueError('From email is not configured.')

    subject, body_html, body_text = render_campaign_email(
        campaign, recipient, include_tracking=include_tracking
    )
    conn = connection or build_smtp_connection()
    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_text,
        from_email=f'{from_name} <{from_email}>',
        to=[recipient.email],
        connection=conn,
    )
    msg.attach_alternative(body_html, 'text/html')
    msg.send()


# 1x1 transparent GIF
TRACKING_GIF_BYTES = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00'
    b',\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)
