from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core.permissions import IsSuperAdmin


class ProtectedSpectacularAPIView(SpectacularAPIView):
    permission_classes = [IsSuperAdmin]


class ProtectedSpectacularSwaggerView(SpectacularSwaggerView):
    permission_classes = [IsSuperAdmin]


class ProtectedSpectacularRedocView(SpectacularRedocView):
    permission_classes = [IsSuperAdmin]
