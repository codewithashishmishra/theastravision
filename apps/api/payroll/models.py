from django.db import models
from organization.models import BaseTenantModel, LegalEntity
from employees.models import Employee
from core.jurisdictions import JURISDICTION_CHOICES, JURISDICTION_IN


class SalaryComponent(BaseTenantModel):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=[('Earning', 'Earning'), ('Deduction', 'Deduction')])
    is_taxable = models.BooleanField(default=True)
    calculation_type = models.CharField(
        max_length=20,
        choices=[('Fixed', 'Fixed'), ('Percentage', 'Percentage'), ('Formula', 'Formula')],
    )
    jurisdiction = models.CharField(max_length=2, choices=JURISDICTION_CHOICES, default=JURISDICTION_IN)


class SalaryStructure(BaseTenantModel):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    ctc = models.DecimalField(max_digits=12, decimal_places=2)
    effective_date = models.DateField()
    components = models.JSONField(default=dict, blank=True)
    variable_pay_enabled = models.BooleanField(
        null=True,
        blank=True,
        help_text='Null inherits tenant setting',
    )
    variable_pay_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Fixed monthly variable pay (INR/USD/CAD)',
    )
    variable_pay_pct = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Fraction of monthly CTC as variable pay (e.g. 0.15)',
    )


class PayrollRun(BaseTenantModel):
    month = models.IntegerField()
    year = models.IntegerField()
    jurisdiction = models.CharField(max_length=2, choices=JURISDICTION_CHOICES, default=JURISDICTION_IN)
    legal_entity = models.ForeignKey(
        LegalEntity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payroll_runs',
    )
    status = models.CharField(
        max_length=20,
        default='Draft',
        choices=[
            ('Draft', 'Draft'),
            ('Processing', 'Processing'),
            ('Approved', 'Approved'),
            ('Locked', 'Locked'),
            ('Released', 'Released'),
        ],
    )
    processed_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)


class Payslip(BaseTenantModel):
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    jurisdiction = models.CharField(max_length=2, choices=JURISDICTION_CHOICES, default=JURISDICTION_IN)
    currency = models.CharField(max_length=3, default='INR')
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    ytd_gross = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    ytd_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_released = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to='payslips/', null=True, blank=True)


class PayrollLineItem(BaseTenantModel):
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='line_items')
    name = models.CharField(max_length=100)
    item_type = models.CharField(max_length=20, choices=[('Earning', 'Earning'), ('Deduction', 'Deduction')])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    statutory_code = models.CharField(max_length=50, blank=True, default='')
    is_employer_contribution = models.BooleanField(default=False)


class TaxDeclaration(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tax_declarations')
    fiscal_year = models.IntegerField()
    jurisdiction = models.CharField(max_length=2, choices=JURISDICTION_CHOICES)
    sections = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        default='Draft',
        choices=[('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Approved', 'Approved')],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'fiscal_year', 'jurisdiction'],
                name='uniq_tax_declaration_employee_fy_jurisdiction',
            ),
        ]


class TaxAiTipUsage(BaseTenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tax_ai_tip_usages')
    period = models.CharField(max_length=7, help_text='Calendar month YYYY-MM')
    jurisdiction = models.CharField(max_length=2, choices=JURISDICTION_CHOICES)
    fiscal_year = models.IntegerField()
    response_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['employee', 'period']),
        ]
