"""Email settings, outbound logs, tracking pixel, and platform health."""

from __future__ import annotations

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.email.outbound import mark_email_opened, notify_tenant_admins_for_email, send_tenant_email
from core.email.sender import resolve_sender
from core.email.smtp_client import TRACKING_GIF_BYTES, test_imap_connection, test_smtp_connection
from core.health_checks import run_all_module_health_checks
from core.models import OutboundEmailLog, Tenant, TenantEmailSettings
from core.permissions import IsPlatformHealthAdmin, IsSuperAdmin, IsTenantEmailAdmin
from core.serializers import (
    OutboundEmailLogSerializer,
    TenantEmailSettingsSerializer,
)
from core.tenant_utils import resolve_request_tenant_id, resolve_tenant_id
from notifications.services import notify_user
from organization.views import BaseTenantViewSet


class EmailTrackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, log_id):
        mark_email_opened(log_id)
        return HttpResponse(TRACKING_GIF_BYTES, content_type='image/gif')


class PlatformModuleHealthView(APIView):
    permission_classes = [IsPlatformHealthAdmin]

    def get(self, request):
        return Response(run_all_module_health_checks())


def _get_or_create_tenant_email_settings(tenant_id):
    tenant = Tenant.objects.filter(pk=tenant_id).first()
    domain = tenant.email_domain if tenant else 'localhost'
    return TenantEmailSettings.objects.get_or_create(
        tenant_id=tenant_id,
        defaults={
            'from_email': f'hr@{domain}',
            'from_name': tenant.name if tenant else 'AastraaHR',
            'notify_roles': ['Company Admin', 'HR Admin'],
        },
    )


class TenantEmailSettingsAPIView(APIView):
    permission_classes = [IsTenantEmailAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        from core.tenant_utils import attach_tenant_to_request

        attach_tenant_to_request(request)

    def get(self, request):
        tenant_id = resolve_request_tenant_id(request)
        if not tenant_id:
            return Response({'detail': 'Tenant context required.'}, status=400)
        obj, _ = _get_or_create_tenant_email_settings(tenant_id)
        data = TenantEmailSettingsSerializer(obj).data
        _, _, _, configured = resolve_sender(tenant_id)
        data['using_platform_fallback'] = not configured
        return Response(data)

    def patch(self, request):
        tenant_id = resolve_request_tenant_id(request)
        if not tenant_id:
            return Response({'detail': 'Tenant context required.'}, status=400)
        obj, _ = _get_or_create_tenant_email_settings(tenant_id)
        serializer = TenantEmailSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TenantEmailSettingsTestSendView(APIView):
    permission_classes = [IsTenantEmailAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        from core.tenant_utils import attach_tenant_to_request

        attach_tenant_to_request(request)

    def post(self, request):
        tenant_id = resolve_request_tenant_id(request)
        if not tenant_id:
            return Response({'detail': 'Tenant context required.'}, status=400)
        to_email = request.data.get('to_email') or request.user.email
        if not to_email:
            return Response({'detail': 'to_email or user email required.'}, status=400)
        _, _, _, configured = resolve_sender(tenant_id)
        log = send_tenant_email(
            tenant_id=tenant_id,
            to=to_email,
            subject='AastraaHR tenant email test',
            body_html='<p>This is a <strong>test email</strong> from your tenant email settings.</p>',
            body_text='This is a test email from your tenant email settings.',
            source='test',
            created_by=request.user,
        )
        notify_user(
            request.user.id,
            tenant_id,
            'Test email sent' if log.status == OutboundEmailLog.STATUS_SENT else 'Test email failed',
            log.subject,
            category='email_sent' if log.status == OutboundEmailLog.STATUS_SENT else 'email_failed',
            link=f'/hr/email-logs?log={log.id}',
            email_log_id=log.id,
        )
        return Response({
            'ok': log.status == OutboundEmailLog.STATUS_SENT,
            'log_id': str(log.id),
            'status': log.status,
            'using_platform_fallback': not configured,
            'smtp_error': log.smtp_error,
        })


class OutboundEmailLogViewSet(BaseTenantViewSet):
    queryset = OutboundEmailLog.objects.select_related('created_by', 'tenant')
    serializer_class = OutboundEmailLogSerializer
    permission_classes = [IsTenantEmailAdmin]
    http_method_names = ['get', 'head', 'options', 'post']

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.role_mappings.filter(
            role__name='Super Admin'
        ).exists():
            qs = OutboundEmailLog.objects.select_related('created_by', 'tenant')
            tenant_id = resolve_request_tenant_id(self.request)
            if tenant_id:
                qs = qs.filter(tenant_id=tenant_id)
        else:
            qs = super().get_queryset()
        params = self.request.query_params
        status_filter = params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        source = params.get('source')
        if source:
            qs = qs.filter(source=source)
        date_from = params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        date_to = params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        search = params.get('search', '').strip()
        if search:
            from django.db.models import Q

            qs = qs.filter(Q(subject__icontains=search) | Q(to_emails__icontains=search))
        return qs

    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        log = self.get_object()
        if log.status not in (OutboundEmailLog.STATUS_SENT, OutboundEmailLog.STATUS_FAILED, OutboundEmailLog.STATUS_OPENED):
            return Response({'detail': 'Cannot resend this log.'}, status=400)
        new_log = send_tenant_email(
            tenant_id=log.tenant_id,
            to=log.to_emails,
            subject=log.subject,
            body_html=log.body_html,
            body_text=log.body_text,
            source='manual_resend',
            source_id=log.source_id,
            created_by=request.user,
            cc=log.cc_emails,
            parent_log=log,
        )
        return Response(OutboundEmailLogSerializer(new_log).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def notify(self, request, pk=None):
        log = self.get_object()
        event = request.data.get('event', 'sent')
        if log.status == OutboundEmailLog.STATUS_FAILED:
            event = 'failed'
        elif log.opened_at:
            event = 'opened'
        notify_tenant_admins_for_email(log.tenant_id, log, event=event)
        return Response({'status': 'ok'})


class EmailSimulateView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        action_type = request.data.get('action', 'imap_poll')
        if action_type == 'imap_poll':
            from cold_campaign.imap_service import poll_inbound_replies

            result = poll_inbound_replies()
            return Response({'ok': True, 'action': action_type, 'result': result})
        return Response({'detail': 'Unknown action.'}, status=400)
