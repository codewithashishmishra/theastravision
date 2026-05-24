from rest_framework import serializers

from core.models import Tenant, TenantAddon


class TenantAddonSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = TenantAddon
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'addon_code',
            'enabled',
            'enabled_at',
            'enabled_by',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('enabled_at', 'enabled_by', 'created_at', 'updated_at')


class TenantAddonUpsertSerializer(serializers.Serializer):
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all())
    addon_code = serializers.ChoiceField(choices=TenantAddon.ADDON_CHOICES)
    enabled = serializers.BooleanField()
    notes = serializers.CharField(required=False, allow_blank=True, default='')
