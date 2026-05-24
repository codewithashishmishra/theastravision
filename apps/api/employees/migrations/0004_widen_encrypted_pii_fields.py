from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_jurisdiction_tax_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employeebank',
            name='account_number',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='employeetax',
            name='pan_number',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='employeetax',
            name='aadhaar_number',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='employeetax',
            name='uan_number',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='employeetax',
            name='pf_number',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='employeetax',
            name='esic_number',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
