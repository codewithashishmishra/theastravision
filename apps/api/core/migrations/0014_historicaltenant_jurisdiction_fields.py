from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_tenant_jurisdiction_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaltenant',
            name='default_currency',
            field=models.CharField(default='INR', max_length=3),
        ),
        migrations.AddField(
            model_name='historicaltenant',
            name='enabled_jurisdictions',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='historicaltenant',
            name='fiscal_year_start_month',
            field=models.IntegerField(default=4),
        ),
    ]
