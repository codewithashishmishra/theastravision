# Generated manually for interview portal overhaul

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0006_recruitment_campaign'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobrequisition',
            name='jd_parse_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('ready', 'Ready'),
                    ('failed', 'Failed'),
                ],
                default='ready',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='jd_parse_error',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='candidate',
            name='resume_parse_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('ready', 'Ready'),
                    ('failed', 'Failed'),
                ],
                default='ready',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='resume_parse_error',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='aiinterviewsession',
            name='session_recording_path',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='aiinterviewsession',
            name='camera_recording_path',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='aiinterviewsession',
            name='recording_started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='aiinterviewsession',
            name='recording_ended_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='aiinterviewsession',
            name='candidate_feedback',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='aiinterviewquestion',
            name='skipped',
            field=models.BooleanField(default=False),
        ),
    ]
