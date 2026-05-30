# Generated manually for Watch Live feature

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('recruitment', '0008_aiinterviewsession_include_assessment'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantRecruitmentSettings',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('interview_recording_retention_days', models.PositiveIntegerField(default=15)),
                ('live_watch_enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recruitment_settings',
                    to='core.tenant',
                )),
            ],
        ),
        migrations.CreateModel(
            name='AiInterviewMediaChunk',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('kind', models.CharField(
                    choices=[
                        ('session_composite', 'Session composite'),
                        ('camera', 'Camera'),
                    ],
                    max_length=32,
                )),
                ('sequence', models.PositiveIntegerField()),
                ('content_type', models.CharField(default='video/webm', max_length=128)),
                ('data', models.BinaryField()),
                ('byte_size', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='media_chunks',
                    to='recruitment.aiinterviewsession',
                )),
            ],
            options={
                'ordering': ['kind', 'sequence'],
            },
        ),
        migrations.CreateModel(
            name='AiInterviewMediaBlob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('kind', models.CharField(
                    choices=[
                        ('session_composite', 'Session composite'),
                        ('camera', 'Camera'),
                        ('answer_audio', 'Answer audio'),
                        ('proctor_image', 'Proctor image'),
                    ],
                    max_length=32,
                )),
                ('question_order', models.PositiveIntegerField(blank=True, null=True)),
                ('content_type', models.CharField(default='application/octet-stream', max_length=128)),
                ('data', models.BinaryField()),
                ('byte_size', models.PositiveIntegerField(default=0)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='media_blobs',
                    to='recruitment.aiinterviewsession',
                )),
            ],
            options={
                'ordering': ['kind', 'question_order'],
            },
        ),
        migrations.AddIndex(
            model_name='aiinterviewmediachunk',
            index=models.Index(fields=['session', 'kind', 'sequence'], name='recruit_chu_sess_kind_seq'),
        ),
        migrations.AddIndex(
            model_name='aiinterviewmediablob',
            index=models.Index(fields=['session', 'kind'], name='recruit_blob_sess_kind'),
        ),
        migrations.AddConstraint(
            model_name='aiinterviewmediachunk',
            constraint=models.UniqueConstraint(
                fields=('session', 'kind', 'sequence'),
                name='uniq_interview_chunk_seq',
            ),
        ),
    ]
