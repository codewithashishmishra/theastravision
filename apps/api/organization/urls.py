from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyProfileViewSet, BranchViewSet, DepartmentViewSet, 
    DesignationViewSet, GradeViewSet, CostCenterViewSet, 
    BusinessUnitViewSet, CompanyCalendarViewSet, HolidayViewSet, 
    EmployeeCodeSequenceViewSet
)

router = DefaultRouter()
router.register(r'profiles', CompanyProfileViewSet, basename='companyprofile')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'designations', DesignationViewSet, basename='designation')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'cost-centers', CostCenterViewSet, basename='costcenter')
router.register(r'business-units', BusinessUnitViewSet, basename='businessunit')
router.register(r'calendars', CompanyCalendarViewSet, basename='companycalendar')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'employee-codes', EmployeeCodeSequenceViewSet, basename='employeecodesequence')

urlpatterns = [
    path('', include(router.urls)),
]
