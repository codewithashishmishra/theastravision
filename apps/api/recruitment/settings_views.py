from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from organization.views import BaseTenantViewSet
from recruitment.models import TenantRecruitmentSettings
from recruitment.serializers import TenantRecruitmentSettingsSerializer


class TenantRecruitmentSettingsViewSet(BaseTenantViewSet):
    queryset = TenantRecruitmentSettings.objects.all()
    serializer_class = TenantRecruitmentSettingsSerializer

    def get_queryset(self):
        tenant_id = getattr(self.request, 'tenant_id', None)
        if not tenant_id:
            return TenantRecruitmentSettings.objects.none()
        return TenantRecruitmentSettings.objects.filter(tenant_id=tenant_id)

    def list(self, request, *args, **kwargs):
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return Response({'error': 'Tenant required.'}, status=status.HTTP_400_BAD_REQUEST)
        settings = TenantRecruitmentSettings.get_for_tenant(tenant_id)
        return Response(TenantRecruitmentSettingsSerializer(settings).data)

    @action(detail=False, methods=['patch'], url_path='update_settings')
    def update_settings(self, request):
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return Response({'error': 'Tenant required.'}, status=status.HTTP_400_BAD_REQUEST)
        settings = TenantRecruitmentSettings.get_for_tenant(tenant_id)
        serializer = TenantRecruitmentSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
