from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalaryComponentViewSet, SalaryStructureViewSet, PayrollRunViewSet, PayslipViewSet

router = DefaultRouter()
router.register(r'components', SalaryComponentViewSet, basename='salary-component')
router.register(r'structures', SalaryStructureViewSet, basename='salary-structure')
router.register(r'runs', PayrollRunViewSet, basename='payroll-run')
router.register(r'payslips', PayslipViewSet, basename='payslip')

urlpatterns = [
    path('', include(router.urls)),
]
