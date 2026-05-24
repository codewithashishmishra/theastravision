from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee
from attendance.models import Shift

class RosterAssignment(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='rosters')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

class ShiftSwapRequest(BaseTenantModel):
    requester = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='swap_requests')
    target_employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='swap_offers')
    date = models.DateField()
    status = models.CharField(max_length=20, default='Pending')

class OvertimeRequest(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='overtimes')
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, default='Pending')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_overtimes')
