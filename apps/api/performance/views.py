from organization.views import BaseTenantViewSet
from .models import Goal, PerformanceReview
from .serializers import GoalSerializer, PerformanceReviewSerializer


class GoalViewSet(BaseTenantViewSet):
    queryset = Goal.objects.select_related('employee').all()
    serializer_class = GoalSerializer


class PerformanceReviewViewSet(BaseTenantViewSet):
    queryset = PerformanceReview.objects.select_related('employee', 'reviewer').all()
    serializer_class = PerformanceReviewSerializer
