from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0002_jurisdiction_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='salarystructure',
            name='variable_pay_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Fixed monthly variable pay (INR/USD/CAD)', max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='salarystructure',
            name='variable_pay_enabled',
            field=models.BooleanField(blank=True, help_text='Null inherits tenant setting', null=True),
        ),
        migrations.AddField(
            model_name='salarystructure',
            name='variable_pay_pct',
            field=models.DecimalField(blank=True, decimal_places=4, help_text='Fraction of monthly CTC as variable pay (e.g. 0.15)', max_digits=5, null=True),
        ),
    ]
