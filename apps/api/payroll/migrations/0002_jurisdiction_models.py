import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0004_legalentity'),
        ('employees', '0003_jurisdiction_tax_profile'),
        ('payroll', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payrollrun',
            name='jurisdiction',
            field=models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], default='IN', max_length=2),
        ),
        migrations.AddField(
            model_name='payrollrun',
            name='legal_entity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payroll_runs', to='organization.legalentity'),
        ),
        migrations.AlterField(
            model_name='payrollrun',
            name='status',
            field=models.CharField(choices=[('Draft', 'Draft'), ('Processing', 'Processing'), ('Approved', 'Approved'), ('Locked', 'Locked'), ('Released', 'Released')], default='Draft', max_length=20),
        ),
        migrations.AddField(
            model_name='salarycomponent',
            name='jurisdiction',
            field=models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], default='IN', max_length=2),
        ),
        migrations.AddField(
            model_name='salarystructure',
            name='components',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='payslip',
            name='currency',
            field=models.CharField(default='INR', max_length=3),
        ),
        migrations.AddField(
            model_name='payslip',
            name='jurisdiction',
            field=models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], default='IN', max_length=2),
        ),
        migrations.AddField(
            model_name='payslip',
            name='pdf_file',
            field=models.FileField(blank=True, null=True, upload_to='payslips/'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='ytd_gross',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='payslip',
            name='ytd_tax',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.CreateModel(
            name='PayrollLineItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('item_type', models.CharField(choices=[('Earning', 'Earning'), ('Deduction', 'Deduction')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('statutory_code', models.CharField(blank=True, default='', max_length=50)),
                ('is_employer_contribution', models.BooleanField(default=False)),
                ('payslip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='line_items', to='payroll.payslip')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
        ),
        migrations.CreateModel(
            name='TaxDeclaration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('fiscal_year', models.IntegerField()),
                ('jurisdiction', models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], max_length=2)),
                ('sections', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(choices=[('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Approved', 'Approved')], default='Draft', max_length=20)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tax_declarations', to='employees.employee')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('employee', 'fiscal_year', 'jurisdiction'), name='uniq_tax_declaration_employee_fy_jurisdiction'),
                ],
            },
        ),
    ]
