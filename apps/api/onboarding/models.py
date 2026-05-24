from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee


class OnboardingChecklist(BaseTenantModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')


class OnboardingTask(BaseTenantModel):
    checklist = models.ForeignKey(OnboardingChecklist, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=100, blank=True, default='')
    sort_order = models.IntegerField(default=0)


class OnboardingAssignment(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='onboarding_assignments')
    checklist = models.ForeignKey(OnboardingChecklist, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='In Progress')
    due_date = models.DateField(null=True, blank=True)


class BGVRecord(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='bgv_records')
    vendor = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, default='Pending')
    report_file = models.FileField(upload_to='bgv_reports/', null=True, blank=True)
    notes = models.TextField(blank=True, default='')
