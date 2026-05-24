import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0004_legalentity'),
        ('employees', '0002_alter_employee_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='payroll_jurisdiction',
            field=models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], default='IN', max_length=2),
        ),
        migrations.AddField(
            model_name='employee',
            name='legal_entity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='organization.legalentity'),
        ),
        migrations.CreateModel(
            name='EmployeeTaxProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('jurisdiction', models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], max_length=2)),
                ('fields', models.JSONField(blank=True, default=dict)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tax_profiles', to='employees.employee')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('employee', 'jurisdiction'), name='uniq_employee_tax_profile_jurisdiction'),
                ],
            },
        ),
    ]
