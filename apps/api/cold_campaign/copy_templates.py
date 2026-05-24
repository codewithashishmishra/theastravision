DEFAULT_SUBJECT = 'Free 3-day AastraaHR trial — simplify HR for {{company}}'

DEFAULT_BODY_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px;">
  <p>Hi{{first_name_greeting}},</p>
  <p>Many HR teams still juggle separate tools for attendance, leave, payroll, and remote work tracking — which slows decisions and creates compliance gaps.</p>
  <p><strong>AastraaHR</strong> brings these workflows into one modern platform built for growing companies: employee records, attendance &amp; shifts, leave, payroll, WFH tracking, and more.</p>
  <p>We would love to show you how teams like yours are streamlining HR operations.</p>
  <p style="margin: 24px 0;">
    <a href="https://theastravision.com" style="background:#2563eb;color:#fff;padding:12px 20px;text-decoration:none;border-radius:6px;display:inline-block;margin-right:12px;">Learn more</a>
    <a href="{{trial_url}}" style="background:#059669;color:#fff;padding:12px 20px;text-decoration:none;border-radius:6px;display:inline-block;">Start 3-day free trial</a>
  </p>
  <p>Happy to answer questions or schedule a short demo at your convenience.</p>
  <p>Best regards,<br>
  <strong>The Astra Vision</strong><br>
  <a href="mailto:sales@theastravision.com">sales@theastravision.com</a><br>
  <a href="https://theastravision.com">theastravision.com</a></p>
  <hr style="border:none;border-top:1px solid #eee;margin-top:32px;">
  <p style="font-size:11px;color:#888;">The Astra Vision · HR technology · Reply STOP to opt out of future emails.</p>
</body>
</html>"""


def apply_merge_tags(text: str, *, first_name: str = '', company: str = '', trial_url: str = '') -> str:
    greeting = f' {first_name}' if first_name else ''
    company_display = company or 'your team'
    return (
        text.replace('{{first_name}}', first_name)
        .replace('{{company}}', company_display)
        .replace('{{first_name_greeting}}', greeting)
        .replace('{{trial_url}}', trial_url)
    )


def default_campaign_copy(trial_url: str = '') -> dict:
    url = trial_url or 'mailto:sales@theastravision.com?subject=AastraaHR%203-day%20trial%20request'
    body = DEFAULT_BODY_HTML.replace('{{trial_url}}', url)
    return {
        'subject': DEFAULT_SUBJECT,
        'body_html': body,
        'body_text': html_to_plain(body),
    }


def html_to_plain(html: str) -> str:
    import re

    text = re.sub(r'<br\s*/?>', '\n', html, flags=re.I)
    text = re.sub(r'</p>', '\n\n', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
