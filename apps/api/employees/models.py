from django.db import models
from core.models import Tenant, User
from organization.models import BaseTenantModel, Branch, Department, Designation, Grade

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
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    reporting_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reportees')
    
    status = models.CharField(max_length=50, default='Active')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_code})"

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
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    account_type = models.CharField(max_length=50, default='Savings')

class EmployeeTax(BaseTenantModel):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='tax_details')
    pan_number = models.CharField(max_length=20)
    aadhaar_number = models.CharField(max_length=20)
    uan_number = models.CharField(max_length=50, null=True, blank=True)
    pf_number = models.CharField(max_length=50, null=True, blank=True)
    esic_number = models.CharField(max_length=50, null=True, blank=True)

class EmployeeDocument(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=100) # e.g., Aadhaar, PAN, Offer Letter
    file = models.FileField(upload_to='employee_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
