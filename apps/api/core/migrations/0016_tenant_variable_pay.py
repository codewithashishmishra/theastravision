from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_rename_core_sal_tenant_created_idx_core_system_tenant__a2d3af_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='allow_employee_variable_override',
            field=models.BooleanField(default=True, help_text='If true, per-employee variable_pay_enabled can override tenant default'),
        ),
        migrations.AddField(
            model_name='tenant',
            name='variable_pay_enabled',
            field=models.BooleanField(default=False, help_text='Company-wide: allow variable pay component in salary structures'),
        ),
        migrations.AddField(
            model_name='historicaltenant',
            name='allow_employee_variable_override',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='historicaltenant',
            name='variable_pay_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
