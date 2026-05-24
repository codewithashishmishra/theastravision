from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExpenseCategoryViewSet, ExpensePolicyViewSet, ExpenseClaimViewSet

router = DefaultRouter()
router.register(r'categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'policies', ExpensePolicyViewSet, basename='expense-policy')
router.register(r'claims', ExpenseClaimViewSet, basename='expense-claim')

urlpatterns = [path('', include(router.urls))]
