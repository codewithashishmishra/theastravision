from organization.views import BaseTenantViewSet
from .models import Ticket
from .serializers import TicketSerializer


class TicketViewSet(BaseTenantViewSet):
    queryset = Ticket.objects.select_related('employee').all()
    serializer_class = TicketSerializer
