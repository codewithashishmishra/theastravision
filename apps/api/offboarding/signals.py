"""Offboarding signals."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Resignation


@receiver(post_save, sender=Resignation)
def schedule_exit_survey(sender, instance, **kwargs):
    """Queue exit survey email when last working date is set."""
    if not instance.last_working_date:
        return
    try:
        from django.core.mail import send_mail
        from django.conf import settings

        employee = instance.employee
        email = getattr(employee.user, 'email', None) if employee.user_id else None
        if not email:
            return
        send_mail(
            subject='Exit survey — share your feedback',
            message=f'Your last working day is {instance.last_working_date}. Please complete our exit survey.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@aastraa.com'),
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        pass
