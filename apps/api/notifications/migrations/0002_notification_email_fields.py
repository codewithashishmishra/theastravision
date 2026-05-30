import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_tenant_email_outbound_log'),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='category',
            field=models.CharField(blank=True, default='general', max_length=32),
        ),
        migrations.AddField(
            model_name='notification',
            name='link',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='notification',
            name='email_log',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='notifications',
                to='core.outboundemaillog',
            ),
        ),
    ]
