"""HR admin endpoints for career portal settings (Job Portal add-on)."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.addons import RequiresTenantAddon
from core.models import TenantAddon
from core.permissions import IsAuthenticatedTenantUser
from recruitment.job_board_auth import generate_api_key
from recruitment.models import TenantCareerPortalSettings
from recruitment.serializers import (
    CareerPortalSettingsSerializer,
    JobRequisitionSerializer,
)


class CareerPortalSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedTenantUser, RequiresTenantAddon(TenantAddon.ADDON_JOB_PORTAL)]

    def _get_or_create_settings(self, tenant_id):
        from django.utils.text import slugify

        from core.models import Tenant

        try:
            return TenantCareerPortalSettings.objects.get(tenant_id=tenant_id), False
        except TenantCareerPortalSettings.DoesNotExist:
            pass
        tenant = Tenant.objects.get(pk=tenant_id)
        base_slug = slugify(tenant.domain or tenant.name)[:80] or 'careers'
        slug = base_slug
        n = 0
        while TenantCareerPortalSettings.objects.filter(slug=slug).exists():
            n += 1
            slug = f'{base_slug}-{n}'
        full_key, prefix, key_hash = generate_api_key()
        settings_obj = TenantCareerPortalSettings.objects.create(
            tenant_id=tenant_id,
            slug=slug,
            api_key_hash=key_hash,
            api_key_prefix=prefix,
        )
        return settings_obj, True

    def _rotate_key(self, settings_obj):
        full_key, prefix, key_hash = generate_api_key()
        settings_obj.api_key_hash = key_hash
        settings_obj.api_key_prefix = prefix
        settings_obj.save(update_fields=['api_key_hash', 'api_key_prefix', 'updated_at'])
        return full_key

    def list(self, request):
        return self._settings_response(request)

    def _settings_response(self, request):
        tenant_id = request.tenant_id
        settings_obj, _ = self._get_or_create_settings(tenant_id)
        data = CareerPortalSettingsSerializer(settings_obj).data
        careers_base = getattr(settings, 'CAREERS_APP_URL', 'http://localhost:3001').rstrip('/')
        cdn_base = getattr(settings, 'JOB_BOARD_CDN_URL', 'http://localhost:4173').rstrip('/')
        data['hosted_careers_url'] = f'{careers_base}/{settings_obj.slug}'
        data['embed_script_url'] = f'{cdn_base}/embed.js'
        return Response(data)

    @action(detail=False, methods=['patch', 'put'])
    def update_settings(self, request):
        tenant_id = request.tenant_id
        settings_obj, _ = self._get_or_create_settings(tenant_id)
        ser = CareerPortalSettingsSerializer(settings_obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return self._settings_response(request)

    @action(detail=False, methods=['post'], url_path='regenerate-key')
    def regenerate_key(self, request):
        tenant_id = request.tenant_id
        settings_obj, _ = self._get_or_create_settings(tenant_id)
        plain = self._rotate_key(settings_obj)
        data = CareerPortalSettingsSerializer(settings_obj).data
        data['api_key'] = plain
        return Response(data)

    @action(detail=False, methods=['get'], url_path='embed-snippet')
    def embed_snippet(self, request):
        tenant_id = request.tenant_id
        settings_obj, _ = self._get_or_create_settings(tenant_id)
        cdn_base = getattr(settings, 'JOB_BOARD_CDN_URL', 'http://localhost:4173').rstrip('/')
        api_base = getattr(settings, 'PUBLIC_API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/') + '/api/v1'
        snippet = (
            f'<script src="{cdn_base}/embed.js" '
            f'data-api-base="{api_base}" '
            f'data-api-key="YOUR_API_KEY" '
            f'data-target="aastraa-job-board"></script>\n'
            f'<div id="aastraa-job-board"></div>'
        )
        return Response({'snippet': snippet, 'slug': settings_obj.slug})


class JobRequisitionCareerMixin:
    """Publish/unpublish actions mixed into JobRequisitionViewSet."""

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        from core.addons import tenant_has_addon
        from core.models import TenantAddon
        from recruitment.job_board_utils import unique_job_slug

        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_has_addon(tenant_id, TenantAddon.ADDON_JOB_PORTAL):
            return Response(
                {'detail': 'Job Portal add-on is not enabled.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        job = self.get_object()
        if job.status != 'Open':
            return Response(
                {'detail': 'Only Open requisitions can be published to the career board.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not job.slug:
            job.slug = unique_job_slug(tenant_id, job.title, exclude_id=job.id)
        job.is_published = True
        job.published_at = timezone.now()
        job.save(update_fields=['slug', 'is_published', 'published_at'])
        return Response(JobRequisitionSerializer(job).data)

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        job = self.get_object()
        job.is_published = False
        job.save(update_fields=['is_published'])
        return Response(JobRequisitionSerializer(job).data)
