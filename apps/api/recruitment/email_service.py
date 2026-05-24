from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from cold_campaign.email_service import build_smtp_connection


def get_frontend_base_url() -> str:
    return getattr(settings, 'FRONTEND_APP_URL', 'http://localhost:3000').rstrip('/')


def send_interview_invite(session) -> None:
    candidate = session.candidate
    job = session.job
    link = f"{get_frontend_base_url()}/interview/join/{session.magic_token}"
    subject = f"AI Interview invitation — {job.title} at AastraaHR"
    body_html = f"""
    <p>Hello {candidate.first_name},</p>
    <p>You have been invited to complete an AI voice interview with <strong>Astra</strong> for the role of <strong>{job.title}</strong>.</p>
    <p>You may answer in English or Hindi; your responses are evaluated in English.</p>
    <p><a href="{link}" style="background:#2563eb;color:#fff;padding:12px 20px;text-decoration:none;border-radius:6px;">Start interview</a></p>
    <p>This link expires at {session.expires_at}.</p>
  """
    body_text = f"Hello {candidate.first_name},\n\nStart your interview: {link}\n"
    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_text,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@aastraahr.com'),
        to=[candidate.email],
        connection=build_smtp_connection(),
    )
    msg.attach_alternative(body_html, 'text/html')
    msg.send()


def send_report_to_hr(session, report) -> None:
    candidate = session.candidate
    job = session.job
    recipients = []
    if job.hiring_manager:
        hm = job.hiring_manager
        email = None
        if hm.user_id and hm.user.email:
            email = hm.user.email
        elif hasattr(hm, 'contact') and hm.contact.personal_email:
            email = hm.contact.personal_email
        if email:
            recipients.append(email)
    if not recipients:
        recipients = [getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@aastraahr.com')]
    link = f"{get_frontend_base_url()}/recruitment/ai-interviews/{session.id}"
    subject = f"AI Interview report — {candidate.first_name} {candidate.last_name} ({job.title})"
    body_html = report.summary_html or f'<p>View report: <a href="{link}">{link}</a></p>'
    msg = EmailMultiAlternatives(
        subject=subject,
        body=f"AI interview report for {candidate.first_name}. View: {link}",
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@aastraahr.com'),
        to=recipients,
        connection=build_smtp_connection(),
    )
    msg.attach_alternative(body_html, 'text/html')
    msg.send()
