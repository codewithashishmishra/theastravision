import uuid

from django.db import models
from django.utils import timezone

from core.models import User
from employees.models import Employee
from organization.models import BaseTenantModel


class WFHPolicy(BaseTenantModel):
    require_hr_approval = models.BooleanField(default=True)
    screenshot_interval_seconds = models.PositiveIntegerField(default=15)
    idle_threshold_seconds = models.PositiveIntegerField(default=300)
    heartbeat_interval_seconds = models.PositiveIntegerField(default=60)
    heartbeat_miss_seconds = models.PositiveIntegerField(default=180)
    screenshot_retention_days = models.PositiveIntegerField(default=30)
    allow_pause = models.BooleanField(default=True)
    capture_window_title = models.BooleanField(default=False)
    max_daily_screenshot_count = models.PositiveIntegerField(default=5000)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "WFH policies"

    @classmethod
    def get_active(cls, tenant_id):
        return cls.objects.filter(tenant_id=tenant_id, is_active=True).first()


class WFHRequest(BaseTenantModel):
    STATUS_PENDING = "pending"
    STATUS_MANAGER_APPROVED = "manager_approved"
    STATUS_HR_APPROVED = "hr_approved"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_MANAGER_APPROVED, "Manager Approved"),
        (STATUS_HR_APPROVED, "HR Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="wfh_requests")
    request_date = models.DateField(default=timezone.localdate)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    approved_by_manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="wfh_manager_approvals"
    )
    approved_by_hr = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="wfh_hr_approvals"
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "employee", "status"]),
            models.Index(fields=["tenant", "start_date", "end_date"]),
        ]

    @property
    def is_wfh_approved(self):
        policy = WFHPolicy.get_active(self.tenant_id)
        if self.status == self.STATUS_HR_APPROVED:
            return True
        if self.status == self.STATUS_MANAGER_APPROVED and policy and not policy.require_hr_approval:
            return True
        return False


class WFHApproval(BaseTenantModel):
    wfh_request = models.ForeignKey(WFHRequest, on_delete=models.CASCADE, related_name="approvals")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    remarks = models.TextField(blank=True)


class EmployeeConsent(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="wfh_consents")
    consent_type = models.CharField(max_length=50, default="wfh_tracking_v1")
    consented_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["employee", "consent_type", "revoked_at"])]


class TrackerDevice(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="tracker_devices")
    device_uuid = models.CharField(max_length=64)
    device_name = models.CharField(max_length=255, blank=True)
    os_name = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=100, blank=True)
    mac_address_hash = models.CharField(max_length=64, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    is_trusted = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("tenant", "device_uuid")
        indexes = [models.Index(fields=["device_uuid"])]


class WorkSession(BaseTenantModel):
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_STOPPED = "stopped"
    STATUS_INTERRUPTED = "interrupted"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_STOPPED, "Stopped"),
        (STATUS_INTERRUPTED, "Interrupted"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="work_sessions")
    wfh_request = models.ForeignKey(WFHRequest, on_delete=models.CASCADE, related_name="work_sessions")
    device = models.ForeignKey(TrackerDevice, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    total_duration = models.PositiveIntegerField(default=0, help_text="Seconds")
    active_duration = models.PositiveIntegerField(default=0, help_text="Seconds")
    idle_duration = models.PositiveIntegerField(default=0, help_text="Seconds")
    paused_duration = models.PositiveIntegerField(default=0, help_text="Seconds")
    screenshot_count = models.PositiveIntegerField(default=0)
    task_title = models.CharField(max_length=255, blank=True)
    task_description = models.TextField(blank=True)
    encryption_key_wrapped = models.TextField(
        null=True,
        blank=True,
        help_text="Per-session AES-256-GCM data key wrapped with server master key",
    )

    class Meta:
        indexes = [
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["tenant", "start_time"]),
        ]


class WorkSessionHeartbeat(BaseTenantModel):
    session = models.ForeignKey(WorkSession, on_delete=models.CASCADE, related_name="heartbeats")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    device = models.ForeignKey(TrackerDevice, on_delete=models.SET_NULL, null=True, blank=True)
    heartbeat_at = models.DateTimeField()
    app_status = models.CharField(max_length=50, default="active")
    battery_status = models.CharField(max_length=50, blank=True)
    network_status = models.CharField(max_length=50, blank=True)

    class Meta:
        indexes = [models.Index(fields=["session", "heartbeat_at"])]


class ScreenshotCapture(BaseTenantModel):
    session = models.ForeignKey(WorkSession, on_delete=models.CASCADE, related_name="screenshots")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    captured_at = models.DateTimeField()
    storage_key = models.CharField(max_length=512)
    thumbnail_key = models.CharField(max_length=512, blank=True)
    monitor_number = models.PositiveSmallIntegerField(default=1)
    file_size = models.PositiveIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64)
    encrypted = models.BooleanField(default=True)
    encryption_algorithm = models.CharField(max_length=32, default="aes-256-gcm")
    window_title = models.CharField(max_length=512, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["session", "captured_at"]),
            models.Index(fields=["employee", "captured_at"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["session", "checksum_sha256"], name="uniq_session_screenshot_checksum"),
        ]


class WorkSessionEvent(BaseTenantModel):
    EVENT_SESSION_START = "session_start"
    EVENT_PAUSE = "pause"
    EVENT_RESUME = "resume"
    EVENT_AUTO_PAUSE = "auto_pause"
    EVENT_IDLE_START = "idle_start"
    EVENT_IDLE_END = "idle_end"
    EVENT_SPOOF_DETECTED = "spoof_detected"
    EVENT_SESSION_STOP = "session_stop"
    EVENT_CHOICES = [
        (EVENT_SESSION_START, "Session start"),
        (EVENT_PAUSE, "Pause"),
        (EVENT_RESUME, "Resume"),
        (EVENT_AUTO_PAUSE, "Auto pause"),
        (EVENT_IDLE_START, "Idle start"),
        (EVENT_IDLE_END, "Idle end"),
        (EVENT_SPOOF_DETECTED, "Spoof detected"),
        (EVENT_SESSION_STOP, "Session stop"),
    ]

    session = models.ForeignKey(WorkSession, on_delete=models.CASCADE, related_name="events")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    occurred_at = models.DateTimeField()
    detail = models.CharField(max_length=512, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["session", "occurred_at"]),
            models.Index(fields=["employee", "occurred_at"]),
        ]


class IdleLog(BaseTenantModel):
    session = models.ForeignKey(WorkSession, on_delete=models.CASCADE, related_name="idle_logs")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    idle_start_time = models.DateTimeField()
    idle_end_time = models.DateTimeField(null=True, blank=True)
    idle_duration = models.PositiveIntegerField(default=0, help_text="Seconds")
    reason = models.CharField(max_length=100, default="threshold_exceeded")


class ActivitySummary(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="activity_summaries")
    session = models.ForeignKey(WorkSession, on_delete=models.CASCADE, null=True, blank=True)
    summary_date = models.DateField()
    active_seconds = models.PositiveIntegerField(default=0)
    idle_seconds = models.PositiveIntegerField(default=0)
    screenshot_count = models.PositiveIntegerField(default=0)
    productivity_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("employee", "summary_date", "session")


class TrackerAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, null=True, blank=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "created_at"])]


class TrackerAppVersion(models.Model):
    version = models.CharField(max_length=50, unique=True)
    min_supported = models.CharField(max_length=50)
    download_url = models.URLField(blank=True)
    release_notes = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class TrackerBugReport(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="tracker_bug_reports")
    description = models.TextField()
    screenshot_key = models.CharField(max_length=512, blank=True)
    status = models.CharField(max_length=20, default="open")
    reported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "reported_at"])]

