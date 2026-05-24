import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_tenant_jurisdiction_fields'),
        ('organization', '0003_org_unique_tenant_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalEntity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('jurisdiction', models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], max_length=2)),
                ('legal_name', models.CharField(max_length=255)),
                ('registration_number', models.CharField(blank=True, max_length=100, null=True)),
                ('tax_id', models.CharField(blank=True, help_text='GSTIN / EIN / BN', max_length=100, null=True)),
                ('payroll_account_ids', models.JSONField(blank=True, default=dict)),
                ('is_default_for_jurisdiction', models.BooleanField(default=False)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('tenant', 'jurisdiction', 'legal_name'), name='uniq_legal_entity_tenant_jurisdiction_name'),
                ],
            },
        ),
    ]
