import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_jurisdiction_tax_profile'),
        ('payroll', '0003_variable_pay'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxAiTipUsage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('period', models.CharField(help_text='Calendar month YYYY-MM', max_length=7)),
                ('jurisdiction', models.CharField(choices=[('IN', 'India'), ('US', 'United States'), ('CA', 'Canada')], max_length=2)),
                ('fiscal_year', models.IntegerField()),
                ('response_snapshot', models.JSONField(blank=True, default=dict)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tax_ai_tip_usages', to='employees.employee')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={
                'indexes': [models.Index(fields=['employee', 'period'], name='payroll_tax_employe_8a1f2c_idx')],
            },
        ),
    ]
