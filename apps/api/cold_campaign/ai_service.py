import json

from core.models import EnvConfiguration

from .copy_templates import html_to_plain


def _get_openai_client():
    cfg = EnvConfiguration.get_cached_config('AI') or {}
    api_key = cfg.get('api_key', '')
    model = cfg.get('model', 'gpt-4o-mini')
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

    return OpenAI(api_key=api_key), model


def generate_campaign_copy(campaign, *, tone: str = 'professional') -> dict:
    """Legacy single-variant rewrite."""
    client, model = _get_openai_client()
    trial_url = campaign.trial_url or 'mailto:sales@theastravision.com?subject=AastraaHR%203-day%20trial%20request'
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
    content = response.choices[0].message.content or '{}'
    data = json.loads(content)
    subject = data.get('subject', campaign.subject)
    body_html = data.get('body_html', campaign.body_html)
    return {
        'subject': subject,
        'body_html': body_html,
        'body_text': html_to_plain(body_html),
    }


def _objective_prompt(objective: str, trial_url: str) -> str:
    base_tags = 'Use merge tags {{first_name}} and {{company}} where appropriate.'
    footer = 'Include footer: "Reply STOP to opt out." Sign off as The Astra Vision / sales@theastravision.com.'
    if objective == 'quick_demo':
        return f"""Write 5 DISTINCT B2B cold email variants for AastraaHR HRMS SaaS.
Objective: quick demo — short emails (under 120 words) focused on booking a 15-minute demo call.
Each variant must use different angle/hook but same goal (schedule a demo).
Include HTML links: Learn more https://theastravision.com and demo/trial CTA: {trial_url}
{base_tags}
{footer}
Return JSON: {{ "variants": [ {{ "subject": "...", "body_html": "<html>..." }}, ... ] }} with exactly 5 variants."""
    return f"""Write 5 DISTINCT B2B cold email variants for AastraaHR HRMS SaaS (attendance, leave, payroll, WFH).
Objective: sales — professional pitch under 200 words, trial-focused.
Each variant must use different angle/hook but same goal (start 3-day trial).
Include HTML links: Learn more https://theastravision.com and trial CTA: {trial_url}
{base_tags}
{footer}
Return JSON: {{ "variants": [ {{ "subject": "...", "body_html": "<html>..." }}, ... ] }} with exactly 5 variants."""


def generate_content_variants(campaign, *, objective: str) -> tuple[list[dict], str]:
    """Returns list of 5 variant dicts and model name used."""
    client, model = _get_openai_client()
    trial_url = campaign.trial_url or 'mailto:sales@theastravision.com?subject=AastraaHR%203-day%20trial%20request'
    prompt = _objective_prompt(objective, trial_url)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                'role': 'system',
                'content': 'You write B2B SaaS cold emails. Output valid JSON only with exactly 5 variants.',
            },
            {'role': 'user', 'content': prompt},
        ],
        response_format={'type': 'json_object'},
    )
    content = response.choices[0].message.content or '{}'
    data = json.loads(content)
    raw_variants = data.get('variants', [])
    if len(raw_variants) < 5:
        raise ValueError(f'AI returned {len(raw_variants)} variants; expected 5.')

    variants = []
    for i, v in enumerate(raw_variants[:5], start=1):
        body_html = v.get('body_html', '')
        variants.append({
            'variant_index': i,
            'subject': v.get('subject', ''),
            'body_html': body_html,
            'body_text': html_to_plain(body_html),
        })
    return variants, model


def classify_reply_snippet(snippet: str) -> str:
    """Classify reply text; keyword-first, optional AI fallback."""
    lower = snippet.lower()
    if any(w in lower for w in ('unsubscribe', 'stop', 'remove me', 'opt out', 'do not contact')):
        return 'unsubscribe'
    if any(w in lower for w in ('schedule', 'calendar', 'book a', 'meeting', 'demo call', 'available')):
        return 'schedule'
    if any(w in lower for w in ('interested', 'tell me more', 'pricing', 'sounds good', 'yes')):
        return 'interested'
    if len(snippet.strip()) > 10:
        return 'replied'
    return 'other'
