from organization.views import BaseTenantViewSet
from .models import Asset, AssetAssignment, AssetWarranty
from .serializers import AssetSerializer, AssetAssignmentSerializer, AssetWarrantySerializer


class AssetViewSet(BaseTenantViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer


class AssetAssignmentViewSet(BaseTenantViewSet):
    queryset = AssetAssignment.objects.select_related('asset', 'employee').all()
    serializer_class = AssetAssignmentSerializer


class AssetWarrantyViewSet(BaseTenantViewSet):
    queryset = AssetWarranty.objects.select_related('asset').all()
    serializer_class = AssetWarrantySerializer
