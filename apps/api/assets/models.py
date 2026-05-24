from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee


class Asset(BaseTenantModel):
    name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='Available')

    def __str__(self):
        return f'{self.name} ({self.serial_number})'


class AssetAssignment(BaseTenantModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='asset_assignments')
    assigned_date = models.DateField()

    def __str__(self):
        return f'{self.asset} -> {self.employee}'


class AssetWarranty(BaseTenantModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='warranties')
    expiry_date = models.DateField()
    provider = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.asset} warranty until {self.expiry_date}'
