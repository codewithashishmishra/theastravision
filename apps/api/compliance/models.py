from django.db import models
from organization.models import BaseTenantModel
from employees.models import Employee
from core.jurisdictions import JURISDICTION_CHOICES


class StatutoryRuleSet(models.Model):
    jurisdiction = models.CharField(max_length=2, choices=JURISDICTION_CHOICES)
    version = models.CharField(max_length=50)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    rules = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_from']

    def __str__(self):
        return f'{self.jurisdiction} {self.version} ({self.effective_from})'


class ComplianceDocument(BaseTenantModel):
    DOC_TYPES = [
        ('FORM16', 'Form 16'),
        ('FORM12BA', 'Form 12BA'),
        ('W2', 'W-2'),
        ('FORM1095C', 'Form 1095-C'),
        ('T4', 'T4'),
        ('RL1', 'RL-1'),
        ('ECR', 'ECR Export'),
        ('FORM941', 'Form 941 Export'),
        ('ITR_ASSIST', 'ITR Assist'),
        ('US_1040_PREP', 'US 1040 Prep'),
        ('CA_T1_PREP', 'CA T1 Prep'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='compliance_documents')
    jurisdiction = models.CharField(max_length=2, choices=JURISDICTION_CHOICES)
    document_type = models.CharField(max_length=20, choices=DOC_TYPES)
    fiscal_year = models.IntegerField()
    file = models.FileField(upload_to='compliance/', null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)


class FilingRecord(BaseTenantModel):
    jurisdiction = models.CharField(max_length=2, choices=JURISDICTION_CHOICES)
    filing_type = models.CharField(max_length=50)
    period_label = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        default='Pending',
        choices=[('Pending', 'Pending'), ('Exported', 'Exported'), ('Filed', 'Filed')],
    )
    export_file = models.FileField(upload_to='filings/', null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
