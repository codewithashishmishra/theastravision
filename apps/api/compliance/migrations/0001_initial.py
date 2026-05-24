import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0013_tenant_jurisdiction_fields'),
        ('employees', '0003_jurisdiction_tax_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatutoryRuleSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jurisdiction', models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], max_length=2)),
                ('version', models.CharField(max_length=50)),
                ('effective_from', models.DateField()),
                ('effective_to', models.DateField(blank=True, null=True)),
                ('rules', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-effective_from'],
            },
        ),
        migrations.CreateModel(
            name='ComplianceDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('jurisdiction', models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], max_length=2)),
                ('document_type', models.CharField(choices=[('FORM16', 'Form 16'), ('W2', 'W-2'), ('T4', 'T4'), ('ECR', 'ECR Export'), ('FORM941', 'Form 941 Export'), ('ITR_ASSIST', 'ITR Assist'), ('US_1040_PREP', 'US 1040 Prep'), ('CA_T1_PREP', 'CA T1 Prep')], max_length=20)),
                ('fiscal_year', models.IntegerField()),
                ('file', models.FileField(blank=True, null=True, upload_to='compliance/')),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='compliance_documents', to='employees.employee')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
        ),
        migrations.CreateModel(
            name='FilingRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('jurisdiction', models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], max_length=2)),
                ('filing_type', models.CharField(max_length=50)),
                ('period_label', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Exported', 'Exported'), ('Filed', 'Filed')], default='Pending', max_length=20)),
                ('export_file', models.FileField(blank=True, null=True, upload_to='filings/')),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
        ),
    ]
