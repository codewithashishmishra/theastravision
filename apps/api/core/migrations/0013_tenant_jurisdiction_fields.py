# Generated manually for multi-region payroll

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_systemauditlog_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='default_currency',
            field=models.CharField(default='INR', max_length=3),
        ),
        migrations.AddField(
            model_name='tenant',
            name='enabled_jurisdictions',
            field=models.JSONField(blank=True, default=list, help_text='Payroll jurisdictions enabled for this tenant: IN, US, CA'),
        ),
        migrations.AddField(
            model_name='tenant',
            name='fiscal_year_start_month',
            field=models.IntegerField(default=4),
        ),
    ]
