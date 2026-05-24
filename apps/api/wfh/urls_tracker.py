from django.urls import path

from wfh import views_tracker

urlpatterns = [
    path("auth/browser/", views_tracker.TrackerBrowserLoginPageView.as_view()),
    path("login/", views_tracker.TrackerLoginView.as_view()),
    path("auth/session/exchange/", views_tracker.TrackerSessionExchangeView.as_view()),
    path("auth/refresh/", views_tracker.TrackerRefreshView.as_view()),
    path("auth/bootstrap/", views_tracker.TrackerAuthBootstrapView.as_view()),
    path("logout/", views_tracker.TrackerLogoutView.as_view()),
    path("profile/", views_tracker.TrackerProfileView.as_view()),
    path("approved-wfh-status/", views_tracker.ApprovedWFHStatusView.as_view()),
    path("consent/", views_tracker.TrackerConsentView.as_view()),
    path("device/register/", views_tracker.DeviceRegisterView.as_view()),
    path("device/status/", views_tracker.DeviceStatusView.as_view()),
    path("session/start/", views_tracker.SessionStartView.as_view()),
    path("session/pause/", views_tracker.SessionPauseView.as_view()),
    path("session/resume/", views_tracker.SessionResumeView.as_view()),
    path("session/report/", views_tracker.SessionReportView.as_view()),
    path("session/stop/", views_tracker.SessionStopView.as_view()),
    path("session/current/", views_tracker.SessionCurrentView.as_view()),
    path("session/heartbeat/", views_tracker.SessionHeartbeatView.as_view()),
    path("sessions/history/", views_tracker.SessionHistoryView.as_view()),
    path("bug-report/", views_tracker.BugReportCreateView.as_view()),
    path("screenshot/upload/", views_tracker.ScreenshotUploadView.as_view()),
    path("idle-log/", views_tracker.IdleLogCreateView.as_view()),
]
