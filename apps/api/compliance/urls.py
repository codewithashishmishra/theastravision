from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import StatutoryRuleSetViewSet, ComplianceDocumentViewSet, FilingRecordViewSet, ComplianceActionViewSet

router = DefaultRouter()
router.register(r'rule-sets', StatutoryRuleSetViewSet, basename='statutory-rule-set')
router.register(r'documents', ComplianceDocumentViewSet, basename='compliance-document')
router.register(r'filings', FilingRecordViewSet, basename='filing-record')
router.register(r'actions', ComplianceActionViewSet, basename='compliance-action')

urlpatterns = [
    path('', include(router.urls)),
]
