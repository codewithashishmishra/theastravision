from celery import shared_task


@shared_task
def send_interview_invite_email(session_id: str):
    from recruitment.models import AiInterviewSession
    from recruitment.email_service import send_interview_invite

    session = AiInterviewSession.objects.select_related('candidate', 'job').get(pk=session_id)
    send_interview_invite(session)
    session.invite_sent_at = __import__('django.utils.timezone', fromlist=['timezone']).timezone.now()
    session.save(update_fields=['invite_sent_at'])


@shared_task
def generate_and_email_report(session_id: str):
    from recruitment.services import finalize_interview_report

    finalize_interview_report(session_id)


@shared_task
def cleanup_expired_sessions():
    from django.utils import timezone
    from recruitment.models import AiInterviewSession

    AiInterviewSession.objects.filter(
        expires_at__lt=timezone.now(),
        status__in=['pending', 'active'],
    ).update(status='expired')
