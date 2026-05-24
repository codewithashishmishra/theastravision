from rest_framework import viewsets
from .models import RosterAssignment, ShiftSwapRequest, OvertimeRequest
from .serializers import RosterAssignmentSerializer, ShiftSwapRequestSerializer, OvertimeRequestSerializer
from organization.views import BaseTenantViewSet

class RosterAssignmentViewSet(BaseTenantViewSet):
    queryset = RosterAssignment.objects.all()
    serializer_class = RosterAssignmentSerializer

class ShiftSwapRequestViewSet(BaseTenantViewSet):
    queryset = ShiftSwapRequest.objects.all()
    serializer_class = ShiftSwapRequestSerializer

class OvertimeRequestViewSet(BaseTenantViewSet):
    queryset = OvertimeRequest.objects.all()
    serializer_class = OvertimeRequestSerializer
