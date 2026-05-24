from django.contrib import admin

from wfh.models import (
    ActivitySummary,
    EmployeeConsent,
    IdleLog,
    ScreenshotCapture,
    TrackerAppVersion,
    TrackerAuditLog,
    TrackerDevice,
    WFHApproval,
    WFHPolicy,
    WFHRequest,
    WorkSession,
    WorkSessionEvent,
    WorkSessionHeartbeat,
)


@admin.register(WFHPolicy)
class WFHPolicyAdmin(admin.ModelAdmin):
    list_display = ("tenant", "require_hr_approval", "screenshot_interval_seconds", "is_active")


@admin.register(WFHRequest)
class WFHRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "start_date", "end_date", "status", "tenant")
    list_filter = ("status",)


admin.site.register(WFHApproval)
admin.site.register(EmployeeConsent)
admin.site.register(TrackerDevice)
admin.site.register(WorkSession)
admin.site.register(WorkSessionHeartbeat)
admin.site.register(WorkSessionEvent)
admin.site.register(ScreenshotCapture)
admin.site.register(IdleLog)
admin.site.register(ActivitySummary)
admin.site.register(TrackerAuditLog)
admin.site.register(TrackerAppVersion)
