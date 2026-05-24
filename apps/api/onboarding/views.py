from organization.views import BaseTenantViewSet
from .models import OnboardingChecklist, OnboardingTask, OnboardingAssignment, BGVRecord
from .serializers import (
    OnboardingChecklistSerializer, OnboardingTaskSerializer,
    OnboardingAssignmentSerializer, BGVRecordSerializer,
)


class OnboardingChecklistViewSet(BaseTenantViewSet):
    queryset = OnboardingChecklist.objects.all()
    serializer_class = OnboardingChecklistSerializer


class OnboardingTaskViewSet(BaseTenantViewSet):
    queryset = OnboardingTask.objects.all()
    serializer_class = OnboardingTaskSerializer


class OnboardingAssignmentViewSet(BaseTenantViewSet):
    queryset = OnboardingAssignment.objects.select_related('employee', 'checklist').all()
    serializer_class = OnboardingAssignmentSerializer


class BGVRecordViewSet(BaseTenantViewSet):
    queryset = BGVRecord.objects.select_related('employee').all()
    serializer_class = BGVRecordSerializer
