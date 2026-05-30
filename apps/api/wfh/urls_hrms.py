from django.urls import path

from wfh import views_hrms

urlpatterns = [
    path("requests/", views_hrms.WFHRequestListCreateView.as_view(), name="wfh-requests"),
    path("requests/my/", views_hrms.WFHRequestListCreateView.as_view(), name="wfh-my-requests"),
    path("requests/all/", views_hrms.WFHRequestTenantListView.as_view()),
    path("requests/pending-approvals/", views_hrms.WFHPendingApprovalsView.as_view()),
    path("requests/<uuid:pk>/manager-approve/", views_hrms.WFHManagerApproveView.as_view()),
    path("requests/<uuid:pk>/hr-approve/", views_hrms.WFHHRApproveView.as_view()),
    path("requests/<uuid:pk>/reject/", views_hrms.WFHRejectView.as_view()),
    path("requests/<uuid:pk>/cancel/", views_hrms.WFHCancelView.as_view()),
    path("policy/", views_hrms.WFHPolicyView.as_view()),
    path("dashboard/", views_hrms.WFHDashboardView.as_view()),
    path("employee-summary/", views_hrms.WFHEmployeeSummaryView.as_view()),
    path("team-summary/", views_hrms.WFHTeamSummaryView.as_view()),
    path("session-report/", views_hrms.WFHSessionReportView.as_view()),
    path("productivity-report/", views_hrms.WFHProductivityReportView.as_view()),
    path("productivity-matrix/", views_hrms.WFHProductivityMatrixView.as_view()),
    path("unproductive-timeline/", views_hrms.WFHUnproductiveTimelineView.as_view()),
    path("admin/productivity-rules/", views_hrms.ProductivityRuleListCreateView.as_view()),
    path("admin/productivity-rules/<uuid:pk>/", views_hrms.ProductivityRuleDetailView.as_view()),
    path("sessions/<uuid:session_id>/screenshots/", views_hrms.SessionScreenshotsView.as_view()),
    path("screenshots/<uuid:pk>/", views_hrms.ScreenshotDetailView.as_view()),
    path("sessions/<uuid:session_id>/idle-summary/", views_hrms.SessionIdleSummaryView.as_view()),
    path("admin/tracker-settings/", views_hrms.TrackerSettingsView.as_view()),
    path("admin/tracker-devices/", views_hrms.TrackerDevicesAdminView.as_view()),
    path("admin/audit-logs/", views_hrms.TrackerAuditLogsView.as_view()),
]
