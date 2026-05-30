from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from core.email.outbound import send_tenant_email
from cold_campaign.email_service import build_smtp_connection
from recruitment.interview_email import render_invite_email


def get_frontend_base_url() -> str:
    return getattr(settings, 'FRONTEND_APP_URL', 'http://localhost:3000').rstrip('/')


def send_interview_invite(session) -> None:
    candidate = session.candidate
    job = session.job
    subject, body_html, body_text = render_invite_email(session)
    flags = session.proctor_flags or {}
    cc = list(flags.get('cc_emails') or [])
    tenant_id = candidate.tenant_id or job.tenant_id
    send_tenant_email(
        tenant_id=tenant_id,
        to=candidate.email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        source='interview_invite',
        source_id=str(session.id),
        cc=cc,
    )


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
