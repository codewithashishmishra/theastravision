from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0004_legalentity'),
    ]

    operations = [
        migrations.AddField(
            model_name='branch',
            name='geofence_radius_meters',
            field=models.PositiveIntegerField(default=50),
        ),
        migrations.AddField(
            model_name='branch',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='branch',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]
