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

    OBJECTIVE_SALES = 'sales'
    OBJECTIVE_QUICK_DEMO = 'quick_demo'
    OBJECTIVE_CHOICES = [
        (OBJECTIVE_SALES, 'Sales'),
        (OBJECTIVE_QUICK_DEMO, 'Quick demo'),
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
    generation_objective = models.CharField(
        max_length=20, choices=OBJECTIVE_CHOICES, blank=True, default=''
    )
    followup_count = models.PositiveSmallIntegerField(default=0)
    followup_delay_days = models.JSONField(default=list, blank=True)
    followup_subject_template = models.CharField(max_length=500, blank=True)
    followup_body_html_template = models.TextField(blank=True)
    selected_content = models.ForeignKey(
        'ColdCampaignContentVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='selected_for_campaigns',
    )
    is_paused = models.BooleanField(default=False)
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


class ColdCampaignContentBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        ColdCampaign,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='content_batches',
    )
    objective = models.CharField(max_length=20, choices=ColdCampaign.OBJECTIVE_CHOICES)
    model = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cold_campaign_content_batches',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ColdCampaignContentVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        ColdCampaignContentBatch,
        on_delete=models.CASCADE,
        related_name='variants',
    )
    variant_index = models.PositiveSmallIntegerField()
    subject = models.CharField(max_length=500)
    body_html = models.TextField()
    body_text = models.TextField(blank=True)

    class Meta:
        ordering = ['variant_index']
        unique_together = [('batch', 'variant_index')]


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

    REPLY_NONE = 'none'
    REPLY_REPLIED = 'replied'
    REPLY_INTERESTED = 'interested'
    REPLY_SCHEDULE = 'schedule'
    REPLY_UNSUBSCRIBE = 'unsubscribe'
    REPLY_OTHER = 'other'
    REPLY_STATUS_CHOICES = [
        (REPLY_NONE, 'None'),
        (REPLY_REPLIED, 'Replied'),
        (REPLY_INTERESTED, 'Interested'),
        (REPLY_SCHEDULE, 'Schedule'),
        (REPLY_UNSUBSCRIBE, 'Unsubscribe'),
        (REPLY_OTHER, 'Other'),
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
    outbound_message_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    open_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    followup_step_sent = models.PositiveSmallIntegerField(default=0)
    next_followup_at = models.DateTimeField(null=True, blank=True)
    reply_status = models.CharField(
        max_length=20, choices=REPLY_STATUS_CHOICES, default=REPLY_NONE
    )
    last_reply_at = models.DateTimeField(null=True, blank=True)
    last_reply_snippet = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['email']
        unique_together = [('campaign', 'email')]

    def __str__(self):
        return f'{self.email} ({self.campaign.name})'

    def ensure_outbound_message_id(self):
        if not self.outbound_message_id:
            self.outbound_message_id = f'<{self.tracking_token}@cold-campaign.aastraa>'
        return self.outbound_message_id


class ColdCampaignThreadMessage(models.Model):
    DIRECTION_OUTBOUND = 'outbound'
    DIRECTION_INBOUND = 'inbound'
    DIRECTION_CHOICES = [
        (DIRECTION_OUTBOUND, 'Outbound'),
        (DIRECTION_INBOUND, 'Inbound'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        ColdCampaignRecipient,
        on_delete=models.CASCADE,
        related_name='thread_messages',
    )
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    subject = models.CharField(max_length=500, blank=True)
    body_text = models.TextField(blank=True)
    received_at = models.DateTimeField()
    imap_uid = models.CharField(max_length=64, blank=True, db_index=True)
    classification = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['received_at']


class ColdCampaignImapState(models.Model):
    """Tracks last processed IMAP UID for deduplication."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mailbox_key = models.CharField(max_length=255, unique=True, default='default')
    last_uid = models.CharField(max_length=64, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)
