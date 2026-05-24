from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from core.views import TenantViewSet, UserViewSet, RoleViewSet, PermissionViewSet, UserRoleMappingViewSet, EnvConfigurationViewSet
from organization.views import (
    CompanyProfileViewSet, BranchViewSet, DepartmentViewSet, DesignationViewSet, 
    GradeViewSet, CostCenterViewSet, BusinessUnitViewSet, 
    CompanyCalendarViewSet, HolidayViewSet, EmployeeCodeSequenceViewSet
)
from core import auth_views, mfa_views, passkey_views, monitoring_views

router = DefaultRouter()

# Core
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'user-roles', UserRoleMappingViewSet, basename='user-role')
router.register(r'env-configs', EnvConfigurationViewSet, basename='env-config')

# Organization
router.register(r'company-profiles', CompanyProfileViewSet, basename='company-profile')
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
    path('api/v1/platform/monitoring/', monitoring_views.PlatformMonitoringView.as_view()),
    
    # Original Legacy simplejwt fallback
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # API endpoints
    path('api/v1/', include(router.urls)),
    path('api/v1/employees/', include('employees.urls')),
    path('api/v1/attendance/', include('attendance.urls')),
    path('api/v1/leave/', include('leave.urls')),
    path('api/v1/shifts/', include('shifts.urls')),
    path('api/v1/payroll/', include('payroll.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/recruitment/', include('recruitment.urls')),
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
    
    # OpenAPI Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
