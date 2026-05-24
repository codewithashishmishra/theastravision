from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_authsession_payload_key_wrapped'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='email_domain',
            field=models.CharField(
                blank=True,
                help_text='Email domain for users in this tenant (e.g. aastraa.com)',
                max_length=255,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='historicaltenant',
            name='email_domain',
            field=models.CharField(
                blank=True,
                help_text='Email domain for users in this tenant (e.g. aastraa.com)',
                max_length=255,
                null=True,
            ),
        ),
    ]
