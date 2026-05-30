import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0005_employee_type_tracking'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recruitment', '0005_candidate_proposed_reporting_manager'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecruitmentCampaign',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('status', models.CharField(
                    choices=[
                        ('draft', 'Draft'),
                        ('sending', 'Sending'),
                        ('sent', 'Sent'),
                        ('paused', 'Paused'),
                    ],
                    default='draft',
                    max_length=32,
                )),
                ('outreach_subject', models.CharField(blank=True, default='', max_length=500)),
                ('outreach_body_html', models.TextField(blank=True, default='')),
                ('outreach_body_text', models.TextField(blank=True, default='')),
                ('send_rate_per_minute', models.PositiveIntegerField(default=10)),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='recruitment_campaigns_created',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('default_reporting_manager', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='recruitment_campaigns',
                    to='employees.employee',
                )),
                ('job', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recruitment_campaign',
                    to='recruitment.jobrequisition',
                )),
                ('tenant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='core.tenant',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='candidate',
            name='campaign',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='candidates',
                to='recruitment.recruitmentcampaign',
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='outreach_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidate',
            name='outreach_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('sent', 'Sent'),
                    ('opened', 'Opened'),
                    ('resume_uploaded', 'Resume uploaded'),
                    ('matched', 'Matched'),
                    ('completed', 'Completed'),
                ],
                default='pending',
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='portal_token',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
