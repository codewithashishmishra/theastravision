from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee


class ExpenseCategory(BaseTenantModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.name} ({self.code})'


class ExpensePolicy(BaseTenantModel):
    name = models.CharField(max_length=255)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.name


class ExpenseClaim(BaseTenantModel):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='expense_claims')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='claims')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    receipt = models.FileField(upload_to='expense_receipts/', null=True, blank=True)

    def __str__(self):
        return f'{self.employee} - {self.amount} ({self.status})'
