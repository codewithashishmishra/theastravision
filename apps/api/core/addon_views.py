from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.addon_serializers import TenantAddonSerializer, TenantAddonUpsertSerializer
from core.models import TenantAddon
from core.permissions import IsSuperAdmin


class TenantAddonViewSet(viewsets.ModelViewSet):
    """Super Admin: enable/disable per-tenant add-ons."""

    queryset = TenantAddon.objects.select_related('tenant', 'enabled_by').all()
    serializer_class = TenantAddonSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['tenant', 'addon_code', 'enabled']

    @action(detail=False, methods=['post'], url_path='upsert')
    def upsert(self, request):
        ser = TenantAddonUpsertSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        addon, _created = TenantAddon.objects.get_or_create(
            tenant=data['tenant'],
            addon_code=data['addon_code'],
            defaults={'enabled': False},
        )
        addon.enabled = data['enabled']
        addon.notes = data.get('notes', addon.notes)
        if data['enabled']:
            addon.enabled_at = timezone.now()
            addon.enabled_by = request.user
        else:
            addon.enabled_at = None
            addon.enabled_by = None
        addon.save()
        return Response(TenantAddonSerializer(addon).data, status=status.HTTP_200_OK)
