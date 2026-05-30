from django.db import models
from organization.models import BaseTenantModel
from core.models import User

class Notification(BaseTenantModel):
    CATEGORY_GENERAL = 'general'
    CATEGORY_EMAIL_SENT = 'email_sent'
    CATEGORY_EMAIL_FAILED = 'email_failed'
    CATEGORY_EMAIL_OPENED = 'email_opened'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    channel = models.CharField(max_length=20, choices=[('In-App', 'In-App'), ('Email', 'Email'), ('SMS', 'SMS'), ('Push', 'Push')], default='In-App')
    category = models.CharField(max_length=32, default=CATEGORY_GENERAL, blank=True)
    link = models.CharField(max_length=500, blank=True, default='')
    email_log = models.ForeignKey(
        'core.OutboundEmailLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
    )
    created_at = models.DateTimeField(auto_now_add=True)

class NotificationPreference(BaseTenantModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
