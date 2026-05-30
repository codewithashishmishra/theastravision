import logging
import smtplib

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.email.smtp_client import get_platform_smtp_config
from core.permissions import IsSuperAdmin

from .ai_service import generate_campaign_copy, generate_content_variants
from .copy_templates import default_campaign_copy, html_to_plain
from .csv_import import parse_recipients_csv
from .email_service import TRACKING_GIF_BYTES, render_campaign_email, send_campaign_email
from .models import (
    ColdCampaign,
    ColdCampaignContentBatch,
    ColdCampaignContentVariant,
    ColdCampaignRecipient,
    ColdCampaignThreadMessage,
)
from .serializers import (
    ApplyVariantSerializer,
    ColdCampaignContentBatchSerializer,
    ColdCampaignDetailSerializer,
    ColdCampaignListSerializer,
    ColdCampaignThreadMessageSerializer,
    ColdCampaignWriteSerializer,
    ContentLibraryVariantSerializer,
    GenerateCopySerializer,
    GenerateVariationsSerializer,
    PreviewSerializer,
)
from .tasks import dispatch_campaign_send, resume_campaign_send

logger = logging.getLogger(__name__)

_SMTP_CONFIG_HINT = (
    'Update PLATFORM_SMTP_PASSWORD in apps/api/.env and run: python manage.py seed_env_config'
)


class ColdCampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperAdmin]
    queryset = ColdCampaign.objects.all().prefetch_related('recipients')
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'list':
            return ColdCampaignListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ColdCampaignWriteSerializer
        return ColdCampaignDetailSerializer

    @action(detail=False, methods=['get'], url_path='content-library')
    def content_library(self, request):
        objective = request.query_params.get('objective')
        qs = ColdCampaignContentVariant.objects.select_related('batch', 'batch__campaign').order_by(
            '-batch__created_at', 'variant_index'
        )[:100]
        if objective:
            qs = qs.filter(batch__objective=objective)
        return Response(ContentLibraryVariantSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='threads')
    def threads_list(self, request):
        qs = (
            ColdCampaignThreadMessage.objects.filter(
                direction=ColdCampaignThreadMessage.DIRECTION_INBOUND
            )
            .select_related('recipient', 'recipient__campaign')
            .order_by('-received_at')[:50]
        )
        return Response(ColdCampaignThreadMessageSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'], url_path='threads')
    def campaign_threads(self, request, pk=None):
        campaign = self.get_object()
        qs = ColdCampaignThreadMessage.objects.filter(
            recipient__campaign=campaign
        ).select_related('recipient', 'recipient__campaign').order_by('-received_at')
        return Response(ColdCampaignThreadMessageSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='generate-variations')
    def generate_variations(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status != ColdCampaign.STATUS_DRAFT:
            return Response(
                {'detail': 'Can only generate content for draft campaigns.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = GenerateVariationsSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        objective = ser.validated_data['objective']
        try:
            variants_data, model_name = generate_content_variants(campaign, objective=objective)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({'detail': f'AI generation failed: {exc}'}, status=500)

        batch = ColdCampaignContentBatch.objects.create(
            campaign=campaign,
            objective=objective,
            model=model_name,
            created_by=request.user,
        )
        for v in variants_data:
            ColdCampaignContentVariant.objects.create(batch=batch, **v)

        campaign.generation_objective = objective
        campaign.save(update_fields=['generation_objective', 'updated_at'])
        return Response(ColdCampaignContentBatchSerializer(batch).data)

    @action(detail=True, methods=['post'], url_path='apply-variant')
    def apply_variant(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status != ColdCampaign.STATUS_DRAFT:
            return Response(
                {'detail': 'Can only apply content to draft campaigns.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = ApplyVariantSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            variant = ColdCampaignContentVariant.objects.select_related('batch').get(
                pk=ser.validated_data['variant_id']
            )
        except ColdCampaignContentVariant.DoesNotExist:
            return Response({'detail': 'Variant not found.'}, status=404)

        campaign.subject = variant.subject
        campaign.body_html = variant.body_html
        campaign.body_text = variant.body_text or html_to_plain(variant.body_html)
        campaign.selected_content = variant
        campaign.generation_objective = variant.batch.objective
        campaign.save(
            update_fields=[
                'subject',
                'body_html',
                'body_text',
                'selected_content',
                'generation_objective',
                'updated_at',
            ]
        )
        return Response(ColdCampaignDetailSerializer(campaign).data)

    @action(detail=True, methods=['post'], url_path='load-default-template')
    def load_default_template(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status not in (ColdCampaign.STATUS_DRAFT,):
            return Response(
                {'detail': 'Cannot edit template after send has started.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        defaults = default_campaign_copy(campaign.trial_url)
        campaign.subject = defaults['subject']
        campaign.body_html = defaults['body_html']
        campaign.body_text = defaults['body_text']
        campaign.save(update_fields=['subject', 'body_html', 'body_text', 'updated_at'])
        return Response(ColdCampaignDetailSerializer(campaign).data)

    @action(detail=True, methods=['post'], url_path='import-recipients')
    def import_recipients(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status != ColdCampaign.STATUS_DRAFT:
            return Response(
                {'detail': 'Recipients can only be imported for draft campaigns.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'CSV file is required (field: file).'}, status=400)
        rows, errors = parse_recipients_csv(file_obj)
        created = 0
        for row in rows:
            _, was_created = ColdCampaignRecipient.objects.get_or_create(
                campaign=campaign,
                email=row['email'],
                defaults={
                    'first_name': row.get('first_name', ''),
                    'company': row.get('company', ''),
                },
            )
            if was_created:
                created += 1
        return Response(
            {
                'imported': created,
                'skipped_duplicates': len(rows) - created,
                'warnings': errors,
                'total_recipients': campaign.total_recipients,
            }
        )

    @action(detail=True, methods=['post'], url_path='generate-copy')
    def generate_copy(self, request, pk=None):
        campaign = self.get_object()
        ser = GenerateCopySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = generate_campaign_copy(campaign, tone=ser.validated_data.get('tone', 'professional'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({'detail': f'AI generation failed: {exc}'}, status=500)
        campaign.subject = result['subject']
        campaign.body_html = result['body_html']
        campaign.body_text = result['body_text']
        campaign.save(update_fields=['subject', 'body_html', 'body_text', 'updated_at'])
        return Response(ColdCampaignDetailSerializer(campaign).data)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        campaign = self.get_object()
        ser = PreviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        class _Recipient:
            first_name = ser.validated_data.get('first_name', '')
            company = ser.validated_data.get('company', '')
            tracking_token = '00000000-0000-0000-0000-000000000000'

        subject, body_html, body_text = render_campaign_email(
            campaign, _Recipient(), include_tracking=False
        )
        return Response({'subject': subject, 'body_html': body_html, 'body_text': body_text})

    @action(detail=True, methods=['post'], url_path='send-test')
    def send_test(self, request, pk=None):
        campaign = self.get_object()
        to_email = request.user.email
        if not to_email:
            return Response({'detail': 'Your user account has no email address.'}, status=400)

        smtp_cfg = get_platform_smtp_config()
        if not smtp_cfg.get('host'):
            return Response(
                {
                    'detail': (
                        'SMTP is not configured. Save SMTP settings under Platform Config '
                        '(/settings/global) or set PLATFORM_SMTP_* in apps/api/.env.'
                    ),
                },
                status=400,
            )
        if smtp_cfg.get('user') and not smtp_cfg.get('password'):
            return Response(
                {'detail': f'SMTP password is missing. {_SMTP_CONFIG_HINT}'},
                status=400,
            )

        recipient = ColdCampaignRecipient(
            email=to_email,
            first_name=request.user.first_name or 'there',
            company='Your Company',
            campaign=campaign,
        )
        try:
            send_campaign_email(campaign, recipient, include_tracking=False)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)
        except smtplib.SMTPAuthenticationError:
            return Response(
                {'detail': f'SMTP authentication failed. {_SMTP_CONFIG_HINT}'},
                status=400,
            )
        except smtplib.SMTPException as exc:
            return Response({'detail': f'SMTP error: {exc}'}, status=400)
        except Exception as exc:
            logger.exception('cold_campaign send_test failed')
            return Response({'detail': str(exc)}, status=500)
        return Response({'detail': f'Test email sent to {to_email}.'})

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status == ColdCampaign.STATUS_SENDING and not campaign.is_paused:
            return Response({'detail': 'Campaign is already sending.'}, status=400)
        if campaign.recipients.filter(status=ColdCampaignRecipient.STATUS_PENDING).count() == 0:
            return Response({'detail': 'No pending recipients.'}, status=400)
        if not campaign.subject or not campaign.body_html:
            return Response({'detail': 'Subject and body are required.'}, status=400)
        campaign.status = ColdCampaign.STATUS_SENDING
        campaign.is_paused = False
        campaign.save(update_fields=['status', 'is_paused', 'updated_at'])
        dispatch_campaign_send.delay(str(campaign.id))
        return Response(
            {
                'detail': 'Campaign send started.',
                'status': campaign.status,
                'pending': campaign.recipients.filter(
                    status=ColdCampaignRecipient.STATUS_PENDING
                ).count(),
            }
        )

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status != ColdCampaign.STATUS_SENDING:
            return Response({'detail': 'Only sending campaigns can be paused.'}, status=400)
        campaign.is_paused = True
        campaign.save(update_fields=['is_paused', 'updated_at'])
        return Response({'detail': 'Campaign paused.', 'is_paused': True})

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status != ColdCampaign.STATUS_SENDING:
            return Response({'detail': 'Only sending campaigns can be resumed.'}, status=400)
        campaign.is_paused = False
        campaign.save(update_fields=['is_paused', 'updated_at'])
        resume_campaign_send.delay(str(campaign.id))
        return Response({'detail': 'Campaign resumed.', 'is_paused': False})

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        campaign = self.get_object()
        recipients = campaign.recipients.all()
        return Response(
            {
                'total_recipients': campaign.total_recipients,
                'sent_count': campaign.sent_count,
                'failed_count': campaign.failed_count,
                'opened_count': campaign.opened_count,
                'open_rate': (
                    round(campaign.opened_count / campaign.sent_count * 100, 1)
                    if campaign.sent_count
                    else 0
                ),
                'recipients': [
                    {
                        'id': str(r.id),
                        'email': r.email,
                        'first_name': r.first_name,
                        'company': r.company,
                        'status': r.status,
                        'sent_at': r.sent_at,
                        'opened_at': r.opened_at,
                        'open_count': r.open_count,
                        'error_message': r.error_message,
                        'reply_status': r.reply_status,
                    }
                    for r in recipients
                ],
            }
        )


class TrackingPixelView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, token):
        try:
            recipient = ColdCampaignRecipient.objects.get(tracking_token=token)
            if recipient.opened_at is None:
                recipient.opened_at = timezone.now()
            recipient.open_count += 1
            recipient.save(update_fields=['opened_at', 'open_count'])
        except ColdCampaignRecipient.DoesNotExist:
            pass
        response = HttpResponse(TRACKING_GIF_BYTES, content_type='image/gif')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        return response
