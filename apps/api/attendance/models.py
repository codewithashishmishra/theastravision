from django.db import models
from organization.models import BaseTenantModel, Branch, CompanyProfile
from employees.models import Employee


class AttendanceSettings(BaseTenantModel):
    """Per-tenant punch configuration (Company Admin)."""
    company_profile = models.OneToOneField(
        CompanyProfile, on_delete=models.CASCADE, related_name='attendance_settings', null=True, blank=True
    )
    default_radius_meters = models.IntegerField(default=50)
    require_gps = models.BooleanField(default=True)
    require_selfie = models.BooleanField(default=False)
    allow_web_punch = models.BooleanField(default=True)
    allow_regularization = models.BooleanField(default=True)


class Shift(BaseTenantModel):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_mins = models.IntegerField(default=15)
    half_day_mins = models.IntegerField(default=240)
    is_default = models.BooleanField(default=False)


class GeoFence(BaseTenantModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='geofences')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_meters = models.IntegerField(default=50)


class AttendanceLog(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_logs')
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Half Day', 'Half Day')],
        default='Present',
    )
    method = models.CharField(
        max_length=20,
        choices=[('QR', 'QR'), ('GPS', 'GPS'), ('Manual', 'Manual'), ('Web', 'Web')],
        default='Web',
    )
    punch_source = models.CharField(
        max_length=20,
        choices=[('Web', 'Web'), ('Mobile', 'Mobile'), ('Biometric', 'Biometric')],
        default='Web',
    )
    device_id = models.CharField(max_length=255, null=True, blank=True)
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    selfie = models.ImageField(upload_to='attendance_selfies/', null=True, blank=True)


class AttendanceRegularization(BaseTenantModel):
    attendance_log = models.ForeignKey(
        AttendanceLog, on_delete=models.CASCADE, related_name='regularizations', null=True, blank=True
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='attendance_regularizations', null=True, blank=True
    )
    reason = models.TextField()
    description = models.TextField(blank=True, default='')
    requested_check_in = models.DateTimeField(null=True, blank=True)
    requested_check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        default='Pending',
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
    )
    approved_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_regularizations'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')
