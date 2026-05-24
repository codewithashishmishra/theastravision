from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ColdCampaignViewSet, TrackingPixelView

router = DefaultRouter()
router.register(r'', ColdCampaignViewSet, basename='cold-campaign')

urlpatterns = [
    path('track/<uuid:token>.gif', TrackingPixelView.as_view(), name='cold-campaign-track'),
    *router.urls,
]
