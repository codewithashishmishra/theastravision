from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet, EmployeeContactViewSet, EmployeeBankViewSet,
    EmployeeTaxViewSet, EmployeeDocumentViewSet
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'contacts', EmployeeContactViewSet, basename='employee-contact')
router.register(r'banks', EmployeeBankViewSet, basename='employee-bank')
router.register(r'taxes', EmployeeTaxViewSet, basename='employee-tax')
router.register(r'documents', EmployeeDocumentViewSet, basename='employee-document')

urlpatterns = [
    path('', include(router.urls)),
]
