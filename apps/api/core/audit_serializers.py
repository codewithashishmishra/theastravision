from rest_framework import serializers

from core.models import AuthSession, SystemAuditLog
from core.serializer_fields import UtcDateTimeField


class SystemAuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    created_at = UtcDateTimeField(read_only=True)

    class Meta:
        model = SystemAuditLog
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "user",
            "user_email",
            "action",
            "module",
            "ip_address",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_tenant_name(self, obj):
        return obj.tenant.name if obj.tenant else None


class AuthSessionSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    tenant_id = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    created_at = UtcDateTimeField(read_only=True)

    class Meta:
        model = AuthSession
        fields = [
            "id",
            "user",
            "user_email",
            "tenant_id",
            "tenant_name",
            "client_type",
            "device_fingerprint",
            "ip_address",
            "user_agent",
            "location_city",
            "location_country",
            "login_method",
            "is_revoked",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_tenant_id(self, obj):
        if obj.user and obj.user.tenant_id:
            return str(obj.user.tenant_id)
        return None

    def get_tenant_name(self, obj):
        if obj.user and getattr(obj.user, "tenant", None):
            return obj.user.tenant.name
        return None
