from django.urls import path
from rest_framework.routers import DefaultRouter

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
    path('assessment/<uuid:token>/', assessment_public, name='assessment-detail'),
    path('assessment/<uuid:token>/start/', assessment_start, name='assessment-start'),
    path('assessment/<uuid:token>/submit/', assessment_submit, name='assessment-submit'),
    path('assessment/<uuid:token>/proctor/', assessment_proctor, name='assessment-proctor'),
] + router.urls
