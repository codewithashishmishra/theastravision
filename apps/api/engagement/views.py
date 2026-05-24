from organization.views import BaseTenantViewSet
from .models import Survey, Announcement
from .serializers import SurveySerializer, AnnouncementSerializer


class SurveyViewSet(BaseTenantViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer


class AnnouncementViewSet(BaseTenantViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
