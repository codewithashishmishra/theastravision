from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet, EmployeeContactViewSet, EmployeeBankViewSet,
    EmployeeTaxViewSet, EmployeeTaxProfileViewSet, EmployeeDocumentViewSet, EmployeeTypeViewSet
)
from .views_me import EmployeeMeView, EmployeeMeBankView, EmployeeMeAssetsView, EmployeeMeWorkLocationView

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'contacts', EmployeeContactViewSet, basename='employee-contact')
router.register(r'banks', EmployeeBankViewSet, basename='employee-bank')
router.register(r'taxes', EmployeeTaxViewSet, basename='employee-tax')
router.register(r'tax-profiles', EmployeeTaxProfileViewSet, basename='employee-tax-profile')
router.register(r'documents', EmployeeDocumentViewSet, basename='employee-document')
router.register(r'employee-types', EmployeeTypeViewSet, basename='employee-type')

urlpatterns = [
    path('me/', EmployeeMeView.as_view(), name='employee-me'),
    path('me/bank/', EmployeeMeBankView.as_view(), name='employee-me-bank'),
    path('me/assets/', EmployeeMeAssetsView.as_view(), name='employee-me-assets'),
    path('me/work-location/', EmployeeMeWorkLocationView.as_view(), name='employee-me-work-location'),
    path('', include(router.urls)),
]
