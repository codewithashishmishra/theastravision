from core.models import EnvConfiguration


def generate_campaign_copy(campaign, *, tone: str = 'professional') -> dict:
    cfg = EnvConfiguration.get_cached_config('AI') or {}
    api_key = cfg.get('api_key', '')
    model = cfg.get('model', 'gpt-5.4-mini')
    provider = cfg.get('provider', 'openai')

    if not api_key:
        raise ValueError(
            'AI is not configured. Add your OpenAI API key under Platform Config → AI settings.'
        )
    if provider != 'openai':
        raise ValueError(f'Unsupported AI provider: {provider}')

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ValueError('openai package is not installed.') from exc

    trial_url = campaign.trial_url or 'mailto:sales@theastravision.com?subject=AastraaHR%203-day%20trial%20request'
    client = OpenAI(api_key=api_key)
    prompt = f"""Write a B2B cold email for AastraaHR, a unified HRMS SaaS (attendance, leave, payroll, WFH tracking).
Tone: {tone}. Under 200 words. Professional, not pushy.
Must include these exact CTAs as HTML links in the body:
1. Learn more: https://theastravision.com
2. Start 3-day free trial: {trial_url}
Use merge tags {{first_name}} and {{company}} where appropriate in subject and body.
Sign off as The Astra Vision / sales@theastravision.com
Include a one-line footer: "Reply STOP to opt out."
Return JSON only with keys: subject, body_html (full simple HTML email with body tag)."""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': 'You write concise B2B SaaS sales emails. Output valid JSON only.'},
            {'role': 'user', 'content': prompt},
        ],
        response_format={'type': 'json_object'},
    )
    import json

    content = response.choices[0].message.content or '{}'
    data = json.loads(content)
    subject = data.get('subject', campaign.subject)
    body_html = data.get('body_html', campaign.body_html)
    from .copy_templates import html_to_plain

    return {
        'subject': subject,
        'body_html': body_html,
        'body_text': html_to_plain(body_html),
    }
