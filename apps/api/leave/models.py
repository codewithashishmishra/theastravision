from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee

class LeaveType(BaseTenantModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    is_paid = models.BooleanField(default=True)
    carry_forward_limit = models.IntegerField(default=0)

class LeavePolicy(BaseTenantModel):
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    annual_allowance = models.FloatField()
    accrual_frequency = models.CharField(max_length=20, choices=[('Monthly', 'Monthly'), ('Yearly', 'Yearly')])

class LeaveBalance(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    balance = models.FloatField(default=0.0)
    year = models.IntegerField()

class LeaveRequest(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, default='Pending', choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')])
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
