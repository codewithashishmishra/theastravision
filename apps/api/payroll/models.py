from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee

class SalaryComponent(BaseTenantModel):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=[('Earning', 'Earning'), ('Deduction', 'Deduction')])
    is_taxable = models.BooleanField(default=True)
    calculation_type = models.CharField(max_length=20, choices=[('Fixed', 'Fixed'), ('Percentage', 'Percentage'), ('Formula', 'Formula')])

class SalaryStructure(BaseTenantModel):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    ctc = models.DecimalField(max_digits=12, decimal_places=2)
    effective_date = models.DateField()

class PayrollRun(BaseTenantModel):
    month = models.IntegerField()
    year = models.IntegerField()
    status = models.CharField(max_length=20, default='Draft', choices=[('Draft', 'Draft'), ('Processing', 'Processing'), ('Approved', 'Approved'), ('Locked', 'Locked')])
    processed_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)

class Payslip(BaseTenantModel):
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    is_released = models.BooleanField(default=False)
