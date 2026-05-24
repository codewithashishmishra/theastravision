from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RosterAssignmentViewSet, ShiftSwapRequestViewSet, OvertimeRequestViewSet

router = DefaultRouter()
router.register(r'rosters', RosterAssignmentViewSet, basename='roster-assignment')
router.register(r'swaps', ShiftSwapRequestViewSet, basename='shift-swap')
router.register(r'overtime', OvertimeRequestViewSet, basename='overtime-request')

urlpatterns = [
    path('', include(router.urls)),
]
