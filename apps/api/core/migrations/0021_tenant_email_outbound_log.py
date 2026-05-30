import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_historicaltenant_subscription_plan_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantEmailSettings',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('from_email', models.EmailField(max_length=254)),
                ('from_name', models.CharField(default='AastraaHR', max_length=255)),
                ('reply_to', models.EmailField(blank=True, default='', max_length=254)),
                ('notify_roles', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='email_settings', to='core.tenant')),
            ],
        ),
        migrations.CreateModel(
            name='OutboundEmailLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('from_email', models.EmailField(max_length=254)),
                ('from_name', models.CharField(blank=True, default='', max_length=255)),
                ('to_emails', models.JSONField(default=list)),
                ('cc_emails', models.JSONField(blank=True, default=list)),
                ('subject', models.CharField(max_length=500)),
                ('body_html', models.TextField(blank=True, default='')),
                ('body_text', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('queued', 'Queued'), ('sent', 'Sent'), ('failed', 'Failed'), ('opened', 'Opened')], default='queued', max_length=20)),
                ('source', models.CharField(default='general', max_length=64)),
                ('source_id', models.CharField(blank=True, default='', max_length=64)),
                ('message_id', models.CharField(blank=True, default='', max_length=500)),
                ('smtp_error', models.TextField(blank=True, default='')),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('opened_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_emails', to=settings.AUTH_USER_MODEL)),
                ('parent_log', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resends', to='core.outboundemaillog')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outbound_emails', to='core.tenant')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='outboundemaillog',
            index=models.Index(fields=['tenant', 'status', '-created_at'], name='core_outbou_tenant__8c4f21_idx'),
        ),
        migrations.AddIndex(
            model_name='outboundemaillog',
            index=models.Index(fields=['tenant', 'source'], name='core_outbou_tenant__a1b2c3_idx'),
        ),
    ]
