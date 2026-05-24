from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShiftViewSet, GeoFenceViewSet, AttendanceLogViewSet,
    AttendanceRegularizationViewSet, AttendanceSettingsView,
)

router = DefaultRouter()
router.register(r'shifts', ShiftViewSet, basename='shift')
router.register(r'geofences', GeoFenceViewSet, basename='geofence')
router.register(r'logs', AttendanceLogViewSet, basename='attendance-log')
router.register(r'regularizations', AttendanceRegularizationViewSet, basename='attendance-regularization')

urlpatterns = [
    path('settings/', AttendanceSettingsView.as_view()),
    path('', include(router.urls)),
]
