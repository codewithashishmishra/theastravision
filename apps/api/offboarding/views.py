from organization.views import BaseTenantViewSet
from .models import Resignation, ClearanceItem
from .serializers import ResignationSerializer, ClearanceItemSerializer


class ResignationViewSet(BaseTenantViewSet):
    queryset = Resignation.objects.select_related('employee').all()
    serializer_class = ResignationSerializer


class ClearanceItemViewSet(BaseTenantViewSet):
    queryset = ClearanceItem.objects.select_related('resignation').all()
    serializer_class = ClearanceItemSerializer
