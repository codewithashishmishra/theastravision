import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wfh", "0003_worksession_task_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkSessionEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_type", models.CharField(
                    choices=[
                        ("session_start", "Session start"),
                        ("pause", "Pause"),
                        ("resume", "Resume"),
                        ("auto_pause", "Auto pause"),
                        ("idle_start", "Idle start"),
                        ("idle_end", "Idle end"),
                        ("spoof_detected", "Spoof detected"),
                        ("session_stop", "Session stop"),
                    ],
                    max_length=32,
                )),
                ("occurred_at", models.DateTimeField()),
                ("detail", models.CharField(blank=True, max_length=512)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="employees.employee")),
                ("session", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="events",
                    to="wfh.worksession",
                )),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.tenant")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["session", "occurred_at"], name="wfh_wse_sess_occ_idx"),
                    models.Index(fields=["employee", "occurred_at"], name="wfh_wse_emp_occ_idx"),
                ],
            },
        ),
    ]
