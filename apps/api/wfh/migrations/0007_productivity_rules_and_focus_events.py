from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("wfh", "0006_worksession_paused_duration"),
    ]

    operations = [
        migrations.AddField(
            model_name="activitysummary",
            name="productive_seconds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="activitysummary",
            name="unproductive_seconds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="ProductivityRule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                (
                    "target_type",
                    models.CharField(
                        choices=[("app", "Application"), ("tab", "Browser tab title"), ("domain", "Domain")],
                        default="app",
                        max_length=16,
                    ),
                ),
                (
                    "match_type",
                    models.CharField(choices=[("exact", "Exact"), ("regex", "Regex")], default="exact", max_length=16),
                ),
                ("pattern", models.CharField(max_length=255)),
                ("is_productive", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "tenant",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.tenant"),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["tenant", "target_type", "is_active"], name="wfh_prodrul_tenant__9d091b_idx"),
                    models.Index(fields=["tenant", "is_productive", "is_active"], name="wfh_prodrul_tenant__c6674c_idx"),
                ]
            },
        ),
        migrations.CreateModel(
            name="WorkSessionFocusEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("application_name", models.CharField(blank=True, max_length=255)),
                ("active_tab_title", models.CharField(blank=True, max_length=512)),
                ("window_title", models.CharField(blank=True, max_length=512)),
                ("focus_seconds", models.PositiveIntegerField(default=0)),
                ("is_productive", models.BooleanField(default=False)),
                (
                    "employee",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="employees.employee"),
                ),
                (
                    "matched_rule",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="focus_events", to="wfh.productivityrule"),
                ),
                (
                    "screenshot",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="focus_events", to="wfh.screenshotcapture"),
                ),
                (
                    "session",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="focus_events", to="wfh.worksession"),
                ),
                (
                    "tenant",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.tenant"),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["session", "occurred_at"], name="wfh_workses_session_568908_idx"),
                    models.Index(fields=["tenant", "employee", "occurred_at"], name="wfh_workses_tenant__e88fe6_idx"),
                    models.Index(fields=["tenant", "is_productive", "occurred_at"], name="wfh_workses_tenant__1d98f1_idx"),
                ]
            },
        ),
    ]
