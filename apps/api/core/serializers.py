from rest_framework import serializers

from core.jurisdictions import normalize_jurisdiction
from .models import (
    Tenant,
    User,
    Role,
    Permission,
    UserRoleMapping,
    EnvConfiguration,
    FeatureFlag,
    TenantEmailSettings,
    OutboundEmailLog,
)
import json


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'

    def validate_enabled_jurisdictions(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = [value]
        if not value:
            return ['IN']
        normalized = []
        for code in value:
            j = normalize_jurisdiction(str(code))
            if j and j not in normalized:
                normalized.append(j)
        if not normalized:
            raise serializers.ValidationError('At least one valid jurisdiction (IN, US, CA) is required.')
        return normalized


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'tenant', 'phone_number', 'is_mfa_enabled', 'is_active']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), write_only=True, many=True, source='permissions'
    )

    class Meta:
        model = Role
        fields = ['id', 'tenant', 'name', 'description', 'permissions', 'permission_ids']


class UserRoleMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRoleMapping
        fields = '__all__'


class EnvConfigurationSerializer(serializers.ModelSerializer):
    config = serializers.JSONField(write_only=True)
    decrypted_config = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EnvConfiguration
        fields = ['id', 'module', 'config', 'decrypted_config', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_decrypted_config(self, obj):
        return obj.get_config()

    def create(self, validated_data):
        config_data = validated_data.pop('config', {})
        instance = EnvConfiguration.objects.create(**validated_data)
        instance.set_config(config_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        config_data = validated_data.pop('config', None)
        instance.module = validated_data.get('module', instance.module)
        if config_data is not None:
            existing = instance.get_config()
            for secret_key in ('password', 'api_key'):
                val = config_data.get(secret_key)
                if secret_key in existing and val in (None, '', '********'):
                    config_data[secret_key] = existing[secret_key]
            instance.set_config({**existing, **config_data})
        instance.save()
        return instance


class TenantEmailSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantEmailSettings
        fields = [
            'id',
            'tenant',
            'from_email',
            'from_name',
            'reply_to',
            'notify_roles',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class OutboundEmailLogSerializer(serializers.ModelSerializer):
    created_by_email = serializers.SerializerMethodField()

    class Meta:
        model = OutboundEmailLog
        fields = [
            'id',
            'tenant',
            'from_email',
            'from_name',
            'to_emails',
            'cc_emails',
            'subject',
            'body_html',
            'body_text',
            'status',
            'source',
            'source_id',
            'message_id',
            'smtp_error',
            'sent_at',
            'opened_at',
            'created_by',
            'created_by_email',
            'parent_log',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_created_by_email(self, obj):
        if obj.created_by_id:
            return obj.created_by.email
        return None


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = '__all__'
