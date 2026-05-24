from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SalaryComponentViewSet,
    SalaryStructureViewSet,
    PayrollRunViewSet,
    PayslipViewSet,
    PayrollLineItemViewSet,
    TaxDeclarationViewSet,
    TaxAiTipsViewSet,
    PayrollSettingsViewSet,
)

router = DefaultRouter()
router.register(r'components', SalaryComponentViewSet, basename='salary-component')
router.register(r'structures', SalaryStructureViewSet, basename='salary-structure')
router.register(r'runs', PayrollRunViewSet, basename='payroll-run')
router.register(r'payslips', PayslipViewSet, basename='payslip')
router.register(r'line-items', PayrollLineItemViewSet, basename='payroll-line-item')
router.register(r'declarations', TaxDeclarationViewSet, basename='tax-declaration')
router.register(r'tax-tips', TaxAiTipsViewSet, basename='tax-tips')

urlpatterns = [
    path('settings/', PayrollSettingsViewSet.as_view({'get': 'list', 'patch': 'partial_update'})),
    path('', include(router.urls)),
]
