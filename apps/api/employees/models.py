from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from core.models import Tenant, User
from core.jurisdictions import JURISDICTION_CHOICES, JURISDICTION_IN
from organization.models import BaseTenantModel, Branch, Department, Designation, Grade, LegalEntity


class EmployeeType(BaseTenantModel):
    """Tenant master: attendance and tracking rules per employee classification."""

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    require_selfie_on_punch = models.BooleanField(default=False)
    require_gps_on_punch = models.BooleanField(default=True)
    enable_live_tracking = models.BooleanField(default=False)
    tracking_interval_minutes = models.PositiveSmallIntegerField(
        default=10,
        validators=[MinValueValidator(5), MaxValueValidator(15)],
    )
    block_punch_near_home = models.BooleanField(default=False)
    home_exclusion_radius_meters = models.PositiveIntegerField(default=200)
    require_office_geofence = models.BooleanField(default=False)
    allow_remote_punch = models.BooleanField(default=False)
    require_home_location = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'code'], name='uniq_employee_type_tenant_code'),
        ]

    def __str__(self):
        return f'{self.name} ({self.code})'


class Employee(BaseTenantModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile', null=True, blank=True)
    employee_code = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    marital_status = models.CharField(max_length=20, null=True, blank=True)
    blood_group = models.CharField(max_length=10, null=True, blank=True)
    
    # Work details
    date_of_joining = models.DateField()
    employee_type = models.ForeignKey(
        EmployeeType,
        on_delete=models.PROTECT,
        related_name='employees',
        null=True,
        blank=True,
    )
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    reporting_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reportees')
    payroll_jurisdiction = models.CharField(
        max_length=2,
        choices=JURISDICTION_CHOICES,
        default=JURISDICTION_IN,
    )
    legal_entity = models.ForeignKey(
        LegalEntity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
    )

    status = models.CharField(max_length=50, default='Active')
    office_location_verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_code})"


class EmployeeWorkLocation(BaseTenantModel):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='work_location')
    home_address = models.TextField(blank=True, default='')
    home_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    home_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def has_home_coordinates(self):
        return self.home_latitude is not None and self.home_longitude is not None


class EmployeeContact(BaseTenantModel):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='contact')
    personal_email = models.EmailField(null=True, blank=True)
    mobile_number = models.CharField(max_length=20)
    alternate_number = models.CharField(max_length=20, null=True, blank=True)
    present_address = models.TextField()
    permanent_address = models.TextField()
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_number = models.CharField(max_length=20)

class EmployeeBank(BaseTenantModel):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='bank_details')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=512)
    ifsc_code = models.CharField(max_length=20)
    account_type = models.CharField(max_length=50, default='Savings')

class EmployeeTax(BaseTenantModel):
    """Legacy India tax record — prefer EmployeeTaxProfile."""

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='tax_details')
    pan_number = models.CharField(max_length=512)
    aadhaar_number = models.CharField(max_length=512)
    uan_number = models.CharField(max_length=512, null=True, blank=True)
    pf_number = models.CharField(max_length=512, null=True, blank=True)
    esic_number = models.CharField(max_length=512, null=True, blank=True)


class EmployeeTaxProfile(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tax_profiles')
    jurisdiction = models.CharField(max_length=2, choices=JURISDICTION_CHOICES)
    fields = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'jurisdiction'],
                name='uniq_employee_tax_profile_jurisdiction',
            ),
        ]

    def __str__(self):
        return f'{self.employee_id} ({self.jurisdiction})'

class EmployeeDocument(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=100) # e.g., Aadhaar, PAN, Offer Letter
    file = models.FileField(upload_to='employee_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
