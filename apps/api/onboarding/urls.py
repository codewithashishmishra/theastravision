from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OnboardingChecklistViewSet, OnboardingTaskViewSet,
    OnboardingAssignmentViewSet, BGVRecordViewSet,
)

router = DefaultRouter()
router.register(r'checklists', OnboardingChecklistViewSet, basename='onboarding-checklist')
router.register(r'tasks', OnboardingTaskViewSet, basename='onboarding-task')
router.register(r'assignments', OnboardingAssignmentViewSet, basename='onboarding-assignment')
router.register(r'bgv', BGVRecordViewSet, basename='bgv-record')

urlpatterns = [path('', include(router.urls))]
