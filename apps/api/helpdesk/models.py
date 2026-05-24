from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee


class Ticket(BaseTenantModel):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    priority = models.CharField(max_length=20, default='Medium')

    def __str__(self):
        return f'{self.subject} ({self.status})'
