from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0005_employee_type_tracking'),
        ('recruitment', '0004_job_portal'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='proposed_reporting_manager',
            field=models.ForeignKey(
                blank=True,
                help_text='Future reporting manager after hire',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='proposed_hires',
                to='employees.employee',
            ),
        ),
    ]
