from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee


class Goal(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255)
    target_date = models.DateField()
    status = models.CharField(max_length=50, default='In Progress')

    def __str__(self):
        return f'{self.title} ({self.employee})'


class PerformanceReview(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='reviews_given')
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    comments = models.TextField(blank=True, default='')
    status = models.CharField(max_length=50, default='Draft')

    def __str__(self):
        return f'Review for {self.employee}'
