from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
import os

from .models import Tenant, User, Role, Permission, UserRoleMapping, EnvConfiguration, FeatureFlag
from .serializers import (
    TenantSerializer, UserSerializer, RoleSerializer,
    PermissionSerializer, UserRoleMappingSerializer, EnvConfigurationSerializer,
    FeatureFlagSerializer
)
from .permissions import IsSuperAdmin, IsTenantIamAdmin
from .audit import AuditViewSetMixin
from .tenant_utils import attach_tenant_to_request, resolve_request_tenant_id, resolve_tenant_id


class TenantViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsSuperAdmin]
    audit_resource = "tenant"

    def perform_create(self, serializer):
        tenant = serializer.save()
        from organization.services.tenant_provisioning import provision_tenant_defaults

        provision_tenant_defaults(tenant)


class BaseIamViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsTenantIamAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        attach_tenant_to_request(request)

    def _effective_tenant_id(self):
        if IsSuperAdmin().has_permission(self.request, self):
            return resolve_request_tenant_id(self.request)
        return resolve_tenant_id(self.request.user)

    def get_queryset(self):
        tenant_id = self._effective_tenant_id()
        if not tenant_id:
            if IsSuperAdmin().has_permission(self.request, self):
                return self.queryset.all()
            return self.queryset.none()
        return self.filter_queryset_by_tenant(self.queryset, tenant_id)

    def filter_queryset_by_tenant(self, queryset, tenant_id):
        raise NotImplementedError

    def perform_create(self, serializer):
        tenant_id = self._effective_tenant_id()
        if not tenant_id:
            raise ValidationError("No tenant assigned to your account.")
        self.save_with_tenant(serializer, tenant_id)

    def save_with_tenant(self, serializer, tenant_id):
        serializer.save(tenant_id=tenant_id)


class UserViewSet(BaseIamViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    audit_resource = "user"

    def filter_queryset_by_tenant(self, queryset, tenant_id):
        return queryset.filter(tenant_id=tenant_id)

    def save_with_tenant(self, serializer, tenant_id):
        serializer.save(tenant_id=tenant_id)


class RoleViewSet(BaseIamViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    audit_resource = "role"

    def filter_queryset_by_tenant(self, queryset, tenant_id):
        return queryset.filter(tenant_id=tenant_id)

    def save_with_tenant(self, serializer, tenant_id):
        serializer.save(tenant_id=tenant_id)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsTenantIamAdmin]


class UserRoleMappingViewSet(BaseIamViewSet):
    queryset = UserRoleMapping.objects.select_related('user', 'role')
    serializer_class = UserRoleMappingSerializer
    audit_resource = "user_role"

    def filter_queryset_by_tenant(self, queryset, tenant_id):
        return queryset.filter(user__tenant_id=tenant_id, role__tenant_id=tenant_id)

    def save_with_tenant(self, serializer, tenant_id):
        user = serializer.validated_data.get('user') or getattr(serializer.instance, 'user', None)
        role = serializer.validated_data.get('role') or getattr(serializer.instance, 'role', None)
        if user and str(user.tenant_id) != str(tenant_id):
            raise ValidationError({'user': 'User must belong to your tenant.'})
        if role and str(role.tenant_id) != str(tenant_id):
            raise ValidationError({'role': 'Role must belong to your tenant.'})
        serializer.save()


class EnvConfigurationViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    queryset = EnvConfiguration.objects.all()
    serializer_class = EnvConfigurationSerializer
    permission_classes = [IsSuperAdmin]
    lookup_field = 'module'
    audit_module = "config"
    audit_resource = "env_config"

    @action(detail=True, methods=['post'], url_path='test')
    def test_connection(self, request, module=None):
        from core.email.outbound import send_tenant_email
        from core.email.smtp_client import test_imap_connection, test_smtp_connection
        from core.models import Tenant
        from core.tenant_utils import resolve_tenant_id

        if module == 'SMTP':
            to_email = request.data.get('to_email') or request.user.email
            if not to_email:
                return Response({'ok': False, 'detail': 'to_email required.'}, status=400)
            result = test_smtp_connection(to_email)
            if result.get('ok'):
                tenant_id = resolve_tenant_id(request.user) or Tenant.objects.order_by('created_at').values_list('id', flat=True).first()
                if tenant_id:
                    send_tenant_email(
                        tenant_id=tenant_id,
                        to=to_email,
                        subject='AastraaHR SMTP platform test',
                        body_html='<p>SMTP platform configuration test succeeded.</p>',
                        body_text='SMTP platform configuration test succeeded.',
                        source='test',
                        created_by=request.user,
                    )
            return Response(result)
        if module == 'IMAP':
            return Response(test_imap_connection())
        return Response({'ok': False, 'detail': f'No test for module {module}.'}, status=400)


class EnvFileView(APIView):
    permission_classes = [IsSuperAdmin]

    def get_env_paths(self):
        from django.conf import settings
        base_dir = settings.BASE_DIR.parent
        return {
            'api': os.path.join(base_dir, 'api', '.env'),
            'ai_service': os.path.join(base_dir, 'ai-service', '.env')
        }

    def get(self, request):
        paths = self.get_env_paths()
        data = {}
        for key, path in paths.items():
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data[key] = f.read()
            else:
                data[key] = ''
        return Response(data)

    def post(self, request):
        paths = self.get_env_paths()
        updates = request.data
        for key, path in paths.items():
            if key in updates:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(updates[key])
        return Response({"status": "success"})



class FeatureFlagViewSet(AuditViewSetMixin, viewsets.ModelViewSet):
    queryset = FeatureFlag.objects.all()
    serializer_class = FeatureFlagSerializer
    permission_classes = [IsSuperAdmin]
    audit_module = "config"
    audit_resource = "feature_flag"
