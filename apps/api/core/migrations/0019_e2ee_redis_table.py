# Generated manually for E2EE session store

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_alter_historicaltenant_allow_employee_variable_override_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Redis",
            fields=[
                ("session_id", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("payload", models.BinaryField()),
                ("expires_at", models.DateTimeField(db_index=True)),
            ],
            options={
                "db_table": "REDIS",
                "indexes": [
                    models.Index(fields=["expires_at"], name="redis_expires_at_idx"),
                ],
            },
        ),
    ]
