# Generated manually for Job Portal career board

import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_tenantaddon'),
        ('recruitment', '0003_ai_interview'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobrequisition',
            name='slug',
            field=models.SlugField(blank=True, default='', max_length=220),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='published_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='employment_type',
            field=models.CharField(
                choices=[
                    ('Full-time', 'Full-time'),
                    ('Part-time', 'Part-time'),
                    ('Contract', 'Contract'),
                    ('Intern', 'Intern'),
                ],
                default='Full-time',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='work_mode',
            field=models.CharField(
                choices=[('On-site', 'On-site'), ('Hybrid', 'Hybrid'), ('Remote', 'Remote')],
                default='On-site',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='apply_deadline',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='external_apply_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='rich_description_html',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.CreateModel(
            name='TenantCareerPortalSettings',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('api_key_hash', models.CharField(max_length=128)),
                ('api_key_prefix', models.CharField(help_text='Display prefix e.g. jb_live_ab12', max_length=16)),
                ('allowed_embed_origins', models.JSONField(blank=True, default=list)),
                ('logo_url', models.URLField(blank=True, default='', max_length=500)),
                ('primary_color', models.CharField(default='#2563eb', max_length=7)),
                ('company_blurb', models.TextField(blank=True, default='')),
                ('custom_domain', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='career_portal_settings', to='core.tenant')),
            ],
        ),
        migrations.AddConstraint(
            model_name='jobrequisition',
            constraint=models.UniqueConstraint(
                condition=~Q(slug=''),
                fields=('tenant', 'slug'),
                name='uniq_job_slug_per_tenant',
            ),
        ),
    ]
