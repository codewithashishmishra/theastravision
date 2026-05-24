from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResignationViewSet, ClearanceItemViewSet

router = DefaultRouter()
router.register(r'resignations', ResignationViewSet, basename='resignation')
router.register(r'clearance-items', ClearanceItemViewSet, basename='clearance-item')

urlpatterns = [path('', include(router.urls))]
