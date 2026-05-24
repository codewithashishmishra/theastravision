from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_authsession_client_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="authsession",
            name="payload_key_wrapped",
            field=models.TextField(
                blank=True,
                help_text="AES-256 session data key wrapped with server master key (GCM)",
                null=True,
            ),
        ),
    ]
