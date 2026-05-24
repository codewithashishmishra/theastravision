from rest_framework import viewsets, permissions
from .models import Tenant, User, Role, Permission, UserRoleMapping, EnvConfiguration
from .serializers import (
    TenantSerializer, UserSerializer, RoleSerializer, 
    PermissionSerializer, UserRoleMappingSerializer, EnvConfigurationSerializer
)
from .permissions import IsSuperAdmin

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.AllowAny]

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.AllowAny]

class UserRoleMappingViewSet(viewsets.ModelViewSet):
    queryset = UserRoleMapping.objects.all()
    serializer_class = UserRoleMappingSerializer
    permission_classes = [permissions.AllowAny]

class EnvConfigurationViewSet(viewsets.ModelViewSet):
    queryset = EnvConfiguration.objects.all()
    serializer_class = EnvConfigurationSerializer
    permission_classes = [IsSuperAdmin]
    lookup_field = 'module'
