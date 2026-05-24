from django.urls import path

from core.audit_views import (
    AdminActionsAuditView,
    AuditExportView,
    LoginSessionsAuditView,
    PlatformAuditLogsView,
)

urlpatterns = [
    path("platform-logs/", PlatformAuditLogsView.as_view()),
    path("admin-actions/", AdminActionsAuditView.as_view()),
    path("login-sessions/", LoginSessionsAuditView.as_view()),
    path("export/", AuditExportView.as_view()),
]
