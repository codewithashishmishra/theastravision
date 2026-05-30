"""Engagement signals: notifications and emails on publish."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Announcement, Survey


@receiver(post_save, sender=Announcement)
def announcement_notify(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from notifications.services import notify_tenant_users

        notify_tenant_users(
            tenant_id=instance.tenant_id,
            title=f'New announcement: {instance.title}',
            body=instance.body[:500] if instance.body else '',
            category='announcement',
        )
    except Exception:
        pass


@receiver(post_save, sender=Survey)
def survey_notify(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from notifications.services import notify_tenant_users

        notify_tenant_users(
            tenant_id=instance.tenant_id,
            title=f'New survey: {instance.title}',
            body='Please complete the survey when you have a moment.',
            category='survey',
        )
    except Exception:
        pass
