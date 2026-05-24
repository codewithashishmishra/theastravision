from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wfh", "0002_gcm_encryption_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="worksession",
            name="task_title",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="worksession",
            name="task_description",
            field=models.TextField(blank=True),
        ),
    ]
