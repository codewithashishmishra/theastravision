"""AI-generated outreach copy for recruitment campaigns."""

from __future__ import annotations

import json

from core.models import EnvConfiguration


def _fallback_copy(title: str, company_name: str) -> dict:
    subject = f'Opportunity: {title} at {company_name}'
    body_html = f"""
    <p>Hello,</p>
    <p>We are hiring for the role of <strong>{title}</strong> at {company_name}.</p>
    <p>Please use your personal link to upload your resume and complete our screening step.
    The link remains valid until your interview process is finished.</p>
    <p>Thank you,<br/>{company_name} Talent Team</p>
    """
    body_text = (
        f'We are hiring for {title} at {company_name}. '
        'Use your personal link to upload your resume and continue the process.'
    )
    return {'subject': subject, 'body_html': body_html.strip(), 'body_text': body_text}


def generate_outreach_copy(title: str, jd_excerpt: str, company_name: str) -> dict:
    cfg = EnvConfiguration.get_cached_config('AI') or {}
    api_key = cfg.get('api_key', '')
    if not api_key:
        return _fallback_copy(title, company_name)

    try:
        from openai import OpenAI
    except ImportError:
        return _fallback_copy(title, company_name)

    model = cfg.get('model', 'gpt-4o-mini')
    excerpt = (jd_excerpt or '')[:4000]
    prompt = f"""Write a professional recruitment outreach email for the role "{title}" at {company_name}.
Job description excerpt:
{excerpt}

Requirements:
- Compelling subject line mentioning the role
- Warm, concise HTML body (under 180 words)
- Mention they will receive a secure personal link to upload their resume
- Do NOT include a URL placeholder; the system adds the button separately
- Sign off as the {company_name} Talent Team
Return JSON only with keys: subject, body_html, body_text (plain text version)."""

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You write HR recruitment emails. Output valid JSON only.'},
                {'role': 'user', 'content': prompt},
            ],
            response_format={'type': 'json_object'},
        )
        data = json.loads(response.choices[0].message.content or '{}')
        subject = data.get('subject') or _fallback_copy(title, company_name)['subject']
        body_html = data.get('body_html') or ''
        body_text = data.get('body_text') or ''
        if not body_html.strip():
            return _fallback_copy(title, company_name)
        return {'subject': subject, 'body_html': body_html, 'body_text': body_text}
    except Exception:
        return _fallback_copy(title, company_name)
