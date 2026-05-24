from organization.views import BaseTenantViewSet
from .models import ExpenseCategory, ExpensePolicy, ExpenseClaim
from .serializers import ExpenseCategorySerializer, ExpensePolicySerializer, ExpenseClaimSerializer


class ExpenseCategoryViewSet(BaseTenantViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer


class ExpensePolicyViewSet(BaseTenantViewSet):
    queryset = ExpensePolicy.objects.all()
    serializer_class = ExpensePolicySerializer


class ExpenseClaimViewSet(BaseTenantViewSet):
    queryset = ExpenseClaim.objects.select_related('employee', 'category').all()
    serializer_class = ExpenseClaimSerializer
