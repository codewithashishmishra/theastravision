from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShiftViewSet, GeoFenceViewSet, AttendanceLogViewSet,
    AttendanceRegularizationViewSet, AttendanceSettingsView, FieldLocationPingViewSet,
)

router = DefaultRouter()
router.register(r'shifts', ShiftViewSet, basename='shift')
router.register(r'geofences', GeoFenceViewSet, basename='geofence')
router.register(r'logs', AttendanceLogViewSet, basename='attendance-log')
router.register(r'regularizations', AttendanceRegularizationViewSet, basename='attendance-regularization')
router.register(r'field-pings', FieldLocationPingViewSet, basename='attendance-field-ping')

urlpatterns = [
    path('settings/', AttendanceSettingsView.as_view()),
    path('', include(router.urls)),
]
