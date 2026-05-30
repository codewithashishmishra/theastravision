from rest_framework import serializers

from wfh.models import (
    ActivitySummary,
    EmployeeConsent,
    IdleLog,
    ProductivityRule,
    ScreenshotCapture,
    TrackerAppVersion,
    TrackerAuditLog,
    TrackerDevice,
    WFHPolicy,
    WFHRequest,
    WorkSession,
    WorkSessionEvent,
    WorkSessionHeartbeat,
    TrackerBugReport,
    WorkSessionFocusEvent,
)


class WFHPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = WFHPolicy
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at")


class WFHRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    is_wfh_approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = WFHRequest
        fields = [
            "id",
            "employee",
            "employee_name",
            "request_date",
            "start_date",
            "end_date",
            "reason",
            "status",
            "approved_by_manager",
            "approved_by_hr",
            "approval_date",
            "remarks",
            "is_wfh_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "status",
            "approved_by_manager",
            "approved_by_hr",
            "approval_date",
            "created_at",
            "updated_at",
        )

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"


class WFHRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WFHRequest
        fields = ("start_date", "end_date", "reason", "request_date")

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError("end_date must be on or after start_date.")
        return attrs


class TrackerDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackerDevice
        fields = "__all__"
        read_only_fields = ("id", "tenant", "employee", "last_seen_at", "created_at", "updated_at")


class WorkSessionSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkSession
        fields = "__all__"
        read_only_fields = (
            "total_duration",
            "active_duration",
            "idle_duration",
            "screenshot_count",
            "created_at",
            "updated_at",
        )

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"


class WorkSessionHeartbeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSessionHeartbeat
        fields = "__all__"


class ScreenshotCaptureSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ScreenshotCapture
        fields = [
            "id",
            "session",
            "employee",
            "captured_at",
            "monitor_number",
            "file_size",
            "checksum_sha256",
            "encrypted",
            "encryption_algorithm",
            "window_title",
            "image_url",
            "created_at",
        ]

    def get_image_url(self, obj):
        return f"/api/v1/wfh/screenshots/{obj.id}/"


class WorkSessionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSessionEvent
        fields = "__all__"
        read_only_fields = ("id", "tenant", "employee", "created_at", "updated_at")


class SessionReportEventSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=32)
    occurred_at = serializers.DateTimeField()
    detail = serializers.CharField(max_length=512, required=False, allow_blank=True)
    metadata = serializers.DictField(required=False, default=dict)


class SessionFocusSegmentSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    application_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    active_tab_title = serializers.CharField(max_length=512, required=False, allow_blank=True)
    window_title = serializers.CharField(max_length=512, required=False, allow_blank=True)
    focus_seconds = serializers.IntegerField(min_value=0, required=False, default=0)


class SessionReportSerializer(serializers.Serializer):
    task_title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    task_description = serializers.CharField(required=False, allow_blank=True)
    totals = serializers.DictField()
    spoof_flags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    events = SessionReportEventSerializer(many=True)
    focus_segments = SessionFocusSegmentSerializer(many=True, required=False, default=list)


class IdleLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdleLog
        fields = "__all__"


class EmployeeConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeConsent
        fields = "__all__"
        read_only_fields = ("id", "tenant", "employee", "consented_at")


class ActivitySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivitySummary
        fields = "__all__"


class ProductivityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductivityRule
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at")


class WorkSessionFocusEventSerializer(serializers.ModelSerializer):
    screenshot_url = serializers.SerializerMethodField()

    class Meta:
        model = WorkSessionFocusEvent
        fields = "__all__"
        read_only_fields = ("id", "tenant", "employee", "created_at", "updated_at")

    def get_screenshot_url(self, obj):
        if not obj.screenshot_id:
            return ""
        return f"/api/v1/wfh/screenshots/{obj.screenshot_id}/"


class TrackerAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackerAuditLog
        fields = "__all__"


class TrackerAppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackerAppVersion
        fields = "__all__"


class TrackerBugReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackerBugReport
        fields = "__all__"
        read_only_fields = ("id", "tenant", "employee", "status", "reported_at", "created_at", "updated_at")


class WorkSessionHistorySerializer(serializers.ModelSerializer):
    active_duration = serializers.SerializerMethodField()
    idle_duration = serializers.SerializerMethodField()
    paused_duration = serializers.SerializerMethodField()

    class Meta:
        model = WorkSession
        fields = (
            "id",
            "start_time",
            "end_time",
            "status",
            "total_duration",
            "active_duration",
            "idle_duration",
            "paused_duration",
            "task_title",
            "screenshot_count",
        )

    def _effective_durations(self, obj):
        active = obj.active_duration or 0
        idle = obj.idle_duration or 0
        paused = getattr(obj, "paused_duration", 0) or 0
        total = obj.total_duration or 0
        if active == 0 and idle == 0 and paused == 0 and total > 0:
            active = total
        return active, idle, paused

    def get_active_duration(self, obj):
        return self._effective_durations(obj)[0]

    def get_idle_duration(self, obj):
        return self._effective_durations(obj)[1]

    def get_paused_duration(self, obj):
        return self._effective_durations(obj)[2]

