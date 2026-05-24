from django.db import models
from organization.models import BaseTenantModel
from core.models import User

class Notification(BaseTenantModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    channel = models.CharField(max_length=20, choices=[('In-App', 'In-App'), ('Email', 'Email'), ('SMS', 'SMS'), ('Push', 'Push')], default='In-App')
    created_at = models.DateTimeField(auto_now_add=True)

class NotificationPreference(BaseTenantModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
