from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee


class Resignation(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='resignations')
    last_working_date = models.DateField()
    reason = models.TextField(blank=True, default='')
    status = models.CharField(max_length=50, default='Pending')

    def __str__(self):
        return f'{self.employee} - {self.last_working_date}'


class ClearanceItem(BaseTenantModel):
    resignation = models.ForeignKey(Resignation, on_delete=models.CASCADE, related_name='clearance_items')
    department = models.CharField(max_length=100)
    item = models.CharField(max_length=255)
    cleared = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.department}: {self.item}'
