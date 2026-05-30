from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from organization.views import BaseTenantViewSet

from .campaign_services import (
    campaign_stats,
    create_campaign_from_request,
    import_candidates_to_campaign,
    regenerate_campaign_copy,
)
from .models import RecruitmentCampaign
from .serializers import RecruitmentCampaignDetailSerializer, RecruitmentCampaignListSerializer
from .tasks import dispatch_campaign_outreach


class RecruitmentCampaignViewSet(BaseTenantViewSet):
    queryset = RecruitmentCampaign.objects.select_related('job', 'default_reporting_manager').all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RecruitmentCampaignDetailSerializer
        return RecruitmentCampaignListSerializer

    def create(self, request, *args, **kwargs):
        from core.tenant_utils import resolve_request_tenant_id

        tenant_id = resolve_request_tenant_id(request)
        title = (request.data.get('title') or '').strip()
        if not title:
            raise ValidationError({'title': 'Campaign title is required.'})
        manager_id = request.data.get('default_reporting_manager')
        if not manager_id:
            raise ValidationError({'default_reporting_manager': 'Reporting manager is required.'})
        jd_file = request.FILES.get('jd_file')
        candidate_file = request.FILES.get('file')
        if not candidate_file:
            raise ValidationError({'file': 'Upload a CSV or Excel file with candidate emails.'})

        campaign = create_campaign_from_request(
            tenant_id=tenant_id,
            user=request.user,
            title=title,
            jd_file=jd_file,
            default_reporting_manager_id=manager_id,
            candidate_file=candidate_file,
        )
        launch = str(request.data.get('launch', '')).lower() in ('1', 'true', 'yes')
        if launch:
            campaign.status = RecruitmentCampaign.STATUS_SENDING
            campaign.save(update_fields=['status', 'updated_at'])
            dispatch_campaign_outreach.delay(str(campaign.id))

        serializer = RecruitmentCampaignDetailSerializer(campaign, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='import-candidates')
    def import_candidates(self, request, pk=None):
        campaign = self.get_object()
        candidate_file = request.FILES.get('file')
        if not candidate_file:
            return Response({'detail': 'Upload a CSV or Excel file with candidate emails.'}, status=400)
        created, warnings = import_candidates_to_campaign(campaign, candidate_file=candidate_file)
        return Response({'imported': created, 'warnings': warnings, 'stats': campaign_stats(campaign)})

    @action(detail=True, methods=['post'], url_path='generate-copy')
    def generate_copy(self, request, pk=None):
        campaign = regenerate_campaign_copy(self.get_object())
        serializer = RecruitmentCampaignDetailSerializer(campaign, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def launch(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status not in (RecruitmentCampaign.STATUS_DRAFT, RecruitmentCampaign.STATUS_PAUSED):
            return Response({'detail': 'Campaign cannot be launched in its current status.'}, status=400)
        pending = campaign.candidates.filter(outreach_status='pending').exists()
        if not pending:
            return Response({'detail': 'No pending candidates to email.'}, status=400)
        campaign.status = RecruitmentCampaign.STATUS_SENDING
        campaign.save(update_fields=['status', 'updated_at'])
        dispatch_campaign_outreach.delay(str(campaign.id))
        return Response({'status': 'sending', 'stats': campaign_stats(campaign)})
