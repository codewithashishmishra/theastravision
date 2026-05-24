from rest_framework import viewsets, permissions
from .models import Tenant, User, Role, Permission, UserRoleMapping, EnvConfiguration, FeatureFlag
from .serializers import (
    TenantSerializer, UserSerializer, RoleSerializer, 
    PermissionSerializer, UserRoleMappingSerializer, EnvConfigurationSerializer,
    FeatureFlagSerializer
)
from .permissions import IsSuperAdmin
from .audit import AuditViewSetMixin

class TenantViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_resource = "tenant"

class UserViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    audit_resource = "user"

class RoleViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.AllowAny]
    audit_resource = "role"

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.AllowAny]

class UserRoleMappingViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    queryset = UserRoleMapping.objects.all()
    serializer_class = UserRoleMappingSerializer
    permission_classes = [permissions.AllowAny]
    audit_resource = "user_role"

class EnvConfigurationViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    queryset = EnvConfiguration.objects.all()
    serializer_class = EnvConfigurationSerializer
    permission_classes = [IsSuperAdmin]
    lookup_field = 'module'
    audit_module = "config"
    audit_resource = "env_config"

class FeatureFlagViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    queryset = FeatureFlag.objects.all()
    serializer_class = FeatureFlagSerializer
    permission_classes = [IsSuperAdmin]
    audit_module = "config"
    audit_resource = "feature_flag"
