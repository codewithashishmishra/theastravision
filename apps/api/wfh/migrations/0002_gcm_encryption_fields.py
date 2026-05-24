from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wfh", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="worksession",
            name="encryption_key_wrapped",
            field=models.TextField(
                blank=True,
                help_text="Per-session AES-256-GCM data key wrapped with server master key",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="screenshotcapture",
            name="encryption_algorithm",
            field=models.CharField(default="aes-256-gcm", max_length=32),
        ),
    ]
