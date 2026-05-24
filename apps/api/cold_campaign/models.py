import uuid

from django.conf import settings
from django.db import models


class ColdCampaign(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_SENDING = 'sending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_SENDING, 'Sending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    subject = models.CharField(max_length=500, blank=True)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)
    from_name = models.CharField(max_length=255, default='The Astra Vision')
    from_email = models.EmailField(blank=True)
    trial_url = models.URLField(
        max_length=500,
        blank=True,
        default='mailto:sales@theastravision.com?subject=AastraaHR%203-day%20trial%20request',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cold_campaigns',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def total_recipients(self):
        return self.recipients.count()

    @property
    def sent_count(self):
        return self.recipients.filter(status=ColdCampaignRecipient.STATUS_SENT).count()

    @property
    def failed_count(self):
        return self.recipients.filter(status=ColdCampaignRecipient.STATUS_FAILED).count()

    @property
    def opened_count(self):
        return self.recipients.filter(opened_at__isnull=False).count()


class ColdCampaignRecipient(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_BOUNCED = 'bounced'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_BOUNCED, 'Bounced'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        ColdCampaign,
        on_delete=models.CASCADE,
        related_name='recipients',
    )
    email = models.EmailField()
    first_name = models.CharField(max_length=120, blank=True)
    company = models.CharField(max_length=255, blank=True)
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    open_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['email']
        unique_together = [('campaign', 'email')]

    def __str__(self):
        return f'{self.email} ({self.campaign.name})'
