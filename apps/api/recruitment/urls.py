from django.urls import path
from rest_framework.routers import DefaultRouter

from .career_portal_views import CareerPortalSettingsViewSet
from .campaign_views import RecruitmentCampaignViewSet
from .portal_views import (
    CampaignPortalParseStatusView,
    CampaignPortalResumeView,
    CampaignPortalVerifyView,
)
from .live_views import AiInterviewChunkStreamView, AiInterviewMediaStreamView
from .tts_views import AiInterviewTtsStreamView
from .settings_views import TenantRecruitmentSettingsViewSet
from .views import (
    AiInterviewReportViewSet,
    AiInterviewSessionViewSet,
    AssessmentPublicViewSet,
    AssessmentTemplateViewSet,
    CandidateViewSet,
    InterviewViewSet,
    JobRequisitionViewSet,
)

router = DefaultRouter()
router.register(r'jobs', JobRequisitionViewSet, basename='jobs')
router.register(r'candidates', CandidateViewSet, basename='candidates')
router.register(r'interviews', InterviewViewSet, basename='interviews')
router.register(r'ai-sessions', AiInterviewSessionViewSet, basename='ai-sessions')
router.register(r'assessment-templates', AssessmentTemplateViewSet, basename='assessment-templates')
router.register(r'ai-reports', AiInterviewReportViewSet, basename='ai-reports')
router.register(r'career-portal/settings', CareerPortalSettingsViewSet, basename='career-portal-settings')
router.register(r'campaigns', RecruitmentCampaignViewSet, basename='recruitment-campaigns')
router.register(r'settings', TenantRecruitmentSettingsViewSet, basename='recruitment-settings')

assessment_public = AssessmentPublicViewSet.as_view({
    'get': 'retrieve_assessment',
})
assessment_start = AssessmentPublicViewSet.as_view({
    'post': 'start_assessment',
})
assessment_submit = AssessmentPublicViewSet.as_view({
    'post': 'submit',
})
assessment_proctor = AssessmentPublicViewSet.as_view({
    'post': 'proctor_snapshot',
})

urlpatterns = [
    path(
        'ai-sessions/<uuid:session_id>/media/<str:kind>/',
        AiInterviewMediaStreamView.as_view(),
        name='ai-session-media',
    ),
    path(
        'ai-sessions/<uuid:session_id>/live/chunks/<str:kind>/<int:sequence>/',
        AiInterviewChunkStreamView.as_view(),
        name='ai-session-chunk',
    ),
    path(
        'ai-sessions/<uuid:session_id>/tts/<int:sequence>/',
        AiInterviewTtsStreamView.as_view(),
        name='ai-session-tts',
    ),
    path(
        'portal/verify/<uuid:token>/',
        CampaignPortalVerifyView.as_view(),
        name='campaign-portal-verify',
    ),
    path(
        'portal/<uuid:token>/resume/',
        CampaignPortalResumeView.as_view(),
        name='campaign-portal-resume',
    ),
    path(
        'portal/<uuid:token>/parse-status/',
        CampaignPortalParseStatusView.as_view(),
        name='campaign-portal-parse-status',
    ),
    path('assessment/<uuid:token>/', assessment_public, name='assessment-detail'),
    path('assessment/<uuid:token>/start/', assessment_start, name='assessment-start'),
    path('assessment/<uuid:token>/submit/', assessment_submit, name='assessment-submit'),
    path('assessment/<uuid:token>/proctor/', assessment_proctor, name='assessment-proctor'),
] + router.urls
