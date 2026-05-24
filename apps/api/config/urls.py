from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from config.schema_views import (
    ProtectedSpectacularAPIView,
    ProtectedSpectacularRedocView,
    ProtectedSpectacularSwaggerView,
)

from core.views import TenantViewSet, UserViewSet, RoleViewSet, PermissionViewSet, UserRoleMappingViewSet, EnvConfigurationViewSet, FeatureFlagViewSet, EnvFileView
from core.addon_views import TenantAddonViewSet
from organization.views import (
    CompanyProfileViewSet, LegalEntityViewSet, BranchViewSet, DepartmentViewSet, DesignationViewSet, 
    GradeViewSet, CostCenterViewSet, BusinessUnitViewSet, 
    CompanyCalendarViewSet, HolidayViewSet, EmployeeCodeSequenceViewSet
)
from core import auth_views, mfa_views, passkey_views, monitoring_views
from core.e2ee.views import E2EEHandshakeView, InternalE2EESessionKeyView, InternalE2EESessionView

router = DefaultRouter()

# Core
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'user-roles', UserRoleMappingViewSet, basename='user-role')
router.register(r'env-configs', EnvConfigurationViewSet, basename='env-config')
router.register(r'feature-flags', FeatureFlagViewSet, basename='feature-flag')
router.register(r'platform/tenant-addons', TenantAddonViewSet, basename='tenant-addon')

# Organization
router.register(r'company-profiles', CompanyProfileViewSet, basename='company-profile')
router.register(r'legal-entities', LegalEntityViewSet, basename='legal-entity')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'designations', DesignationViewSet, basename='designation')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'cost-centers', CostCenterViewSet, basename='cost-center')
router.register(r'business-units', BusinessUnitViewSet, basename='business-unit')
router.register(r'calendars', CompanyCalendarViewSet, basename='calendar')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'employee-code-sequences', EmployeeCodeSequenceViewSet, basename='employee-code-sequence')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/v1/public/e2ee/handshake/', E2EEHandshakeView.as_view()),
    path('api/v1/internal/e2ee/session/<str:session_id>/', InternalE2EESessionView.as_view()),
    path('api/v1/internal/e2ee/session/<str:session_id>/key/', InternalE2EESessionKeyView.as_view()),

    # Advanced Multi-Auth Endpoints
    path('api/v1/auth/login/password/', auth_views.LoginPasswordView.as_view()),
    path('api/v1/auth/me/', auth_views.MeView.as_view()),
    path('api/v1/auth/token/refresh/', auth_views.RefreshTokenView.as_view()),
    path('api/v1/auth/logout/', auth_views.LogoutView.as_view()),
    
    # TOTP Endpoints
    path('api/v1/auth/totp/setup/', mfa_views.TOTPSetupView.as_view()),
    path('api/v1/auth/totp/verify-setup/', mfa_views.TOTPVerifySetupView.as_view()),
    path('api/v1/auth/totp/verify-login/', mfa_views.TOTPVerifyLoginView.as_view()),
    
    # Face Recognition (OpenCV Biometrics)
    path('api/v1/auth/face/login/', mfa_views.FaceLoginView.as_view()),
    
    # Passkey Endpoints
    path('api/v1/auth/passkey/register/options/', passkey_views.PasskeyRegisterOptions.as_view()),
    path('api/v1/auth/passkey/register/verify/', passkey_views.PasskeyRegisterVerify.as_view()),
    path('api/v1/auth/passkey/login/options/', passkey_views.PasskeyLoginOptions.as_view()),
    path('api/v1/auth/passkey/login/verify/', passkey_views.PasskeyLoginVerify.as_view()),
    
    # Platform Monitoring & cooldown status
    path('api/v1/platform/status/', monitoring_views.PlatformStatusView.as_view()),
    path('api/v1/platform/frontend-debug-log/', monitoring_views.FrontendDebugLogView.as_view()),
    path('api/v1/platform/monitoring/', monitoring_views.PlatformMonitoringView.as_view()),
    path('api/v1/platform/metrics/', monitoring_views.PlatformMetricsView.as_view()),
    path('api/v1/platform/services/', monitoring_views.PlatformServicesView.as_view()),
    path('api/v1/platform/system-logs/', monitoring_views.PlatformSystemLogsView.as_view()),
    path('api/v1/platform/system-logs/export/', monitoring_views.PlatformSystemLogsExportView.as_view()),
    path('api/v1/audit/', include('core.audit_urls')),
    
    # API endpoints
    path('api/v1/', include(router.urls)),
    path('api/v1/config/env-file/', EnvFileView.as_view(), name='env-file'),
    path('api/v1/employees/', include('employees.urls')),
    path('api/v1/attendance/', include('attendance.urls')),
    path('api/v1/leave/', include('leave.urls')),
    path('api/v1/shifts/', include('shifts.urls')),
    path('api/v1/payroll/', include('payroll.urls')),
    path('api/v1/compliance/', include('compliance.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/recruitment/', include('recruitment.urls')),
    path('api/v1/public/job-board/', include('recruitment.public_urls')),
    path('api/v1/wfh/', include('wfh.urls_hrms')),
    path('api/v1/tracker/', include('wfh.urls_tracker')),
    path('api/v1/onboarding/', include('onboarding.urls')),
    path('api/v1/expenses/', include('expenses.urls')),
    path('api/v1/assets/', include('assets.urls')),
    path('api/v1/helpdesk/', include('helpdesk.urls')),
    path('api/v1/performance/', include('performance.urls')),
    path('api/v1/engagement/', include('engagement.urls')),
    path('api/v1/offboarding/', include('offboarding.urls')),
    path('api/v1/dashboards/', include('dashboards.urls')),
    path('api/v1/cold-campaigns/', include('cold_campaign.urls')),
]

if settings.OPENAPI_ENABLED:
    urlpatterns += [
        path('api/schema/', ProtectedSpectacularAPIView.as_view(), name='schema'),
        path('api/schema/swagger-ui/', ProtectedSpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/schema/redoc/', ProtectedSpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
