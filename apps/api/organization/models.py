from django.db import models
import uuid
from core.models import Tenant

class BaseTenantModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CompanyProfile(BaseTenantModel):
    legal_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    tax_id = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    logo = models.FileField(upload_to='company_logos/', null=True, blank=True)

    def __str__(self):
        return self.legal_name

class Branch(BaseTenantModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    timezone = models.CharField(max_length=100, default='UTC')
    is_head_office = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Department(BaseTenantModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_departments')
    head = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')

    def __str__(self):
        return self.name

class Designation(BaseTenantModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Grade(BaseTenantModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    level = models.IntegerField(help_text="Hierarchy level (e.g., 1 for entry, 10 for exec)")

    def __str__(self):
        return self.name

class CostCenter(BaseTenantModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.code})"

class BusinessUnit(BaseTenantModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    head = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_bus')

    def __str__(self):
        return self.name

class CompanyCalendar(BaseTenantModel):
    year = models.IntegerField()
    name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.year})"

class Holiday(BaseTenantModel):
    calendar = models.ForeignKey(CompanyCalendar, on_delete=models.CASCADE, related_name='holidays')
    date = models.DateField()
    name = models.CharField(max_length=255)
    is_optional = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} on {self.date}"

class EmployeeCodeSequence(BaseTenantModel):
    prefix = models.CharField(max_length=10)
    current_value = models.IntegerField(default=0)
    padding = models.IntegerField(default=4)

    def __str__(self):
        return f"{self.prefix} - {self.current_value}"
