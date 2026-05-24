from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, AssetAssignmentViewSet, AssetWarrantyViewSet

router = DefaultRouter()
router.register(r'items', AssetViewSet, basename='asset')
router.register(r'assignments', AssetAssignmentViewSet, basename='asset-assignment')
router.register(r'warranties', AssetWarrantyViewSet, basename='asset-warranty')

urlpatterns = [path('', include(router.urls))]
