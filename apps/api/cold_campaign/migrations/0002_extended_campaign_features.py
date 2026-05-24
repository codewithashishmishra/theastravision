# Generated manually for extended cold campaign features

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cold_campaign', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ColdCampaignContentBatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('objective', models.CharField(choices=[('sales', 'Sales'), ('quick_demo', 'Quick demo')], max_length=20)),
                ('model', models.CharField(blank=True, max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='content_batches', to='cold_campaign.coldcampaign')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cold_campaign_content_batches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ColdCampaignContentVariant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('variant_index', models.PositiveSmallIntegerField()),
                ('subject', models.CharField(max_length=500)),
                ('body_html', models.TextField()),
                ('body_text', models.TextField(blank=True)),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='cold_campaign.coldcampaigncontentbatch')),
            ],
            options={
                'ordering': ['variant_index'],
                'unique_together': {('batch', 'variant_index')},
            },
        ),
        migrations.AddField(
            model_name='coldcampaign',
            name='followup_body_html_template',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='coldcampaign',
            name='followup_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='coldcampaign',
            name='followup_delay_days',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='coldcampaign',
            name='followup_subject_template',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='coldcampaign',
            name='generation_objective',
            field=models.CharField(blank=True, choices=[('sales', 'Sales'), ('quick_demo', 'Quick demo')], default='', max_length=20),
        ),
        migrations.AddField(
            model_name='coldcampaign',
            name='is_paused',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='coldcampaign',
            name='selected_content',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='selected_for_campaigns', to='cold_campaign.coldcampaigncontentvariant'),
        ),
        migrations.AddField(
            model_name='coldcampaignrecipient',
            name='followup_step_sent',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='coldcampaignrecipient',
            name='last_reply_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='coldcampaignrecipient',
            name='last_reply_snippet',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='coldcampaignrecipient',
            name='next_followup_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='coldcampaignrecipient',
            name='outbound_message_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='coldcampaignrecipient',
            name='reply_status',
            field=models.CharField(choices=[('none', 'None'), ('replied', 'Replied'), ('interested', 'Interested'), ('schedule', 'Schedule'), ('unsubscribe', 'Unsubscribe'), ('other', 'Other')], default='none', max_length=20),
        ),
        migrations.CreateModel(
            name='ColdCampaignThreadMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('direction', models.CharField(choices=[('outbound', 'Outbound'), ('inbound', 'Inbound')], max_length=10)),
                ('subject', models.CharField(blank=True, max_length=500)),
                ('body_text', models.TextField(blank=True)),
                ('received_at', models.DateTimeField()),
                ('imap_uid', models.CharField(blank=True, db_index=True, max_length=64)),
                ('classification', models.CharField(blank=True, max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='thread_messages', to='cold_campaign.coldcampaignrecipient')),
            ],
            options={
                'ordering': ['received_at'],
            },
        ),
        migrations.CreateModel(
            name='ColdCampaignImapState',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('mailbox_key', models.CharField(default='default', max_length=255, unique=True)),
                ('last_uid', models.CharField(blank=True, default='', max_length=64)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
