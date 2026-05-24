from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SurveyViewSet, AnnouncementViewSet

router = DefaultRouter()
router.register(r'surveys', SurveyViewSet, basename='engagement-survey')
router.register(r'announcements', AnnouncementViewSet, basename='engagement-announcement')

urlpatterns = [path('', include(router.urls))]
