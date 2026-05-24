# Generated manually for Job Portal add-on

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_tenant_variable_pay'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantAddon',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('addon_code', models.CharField(choices=[('job_portal', 'Job Portal & Career Board SDK')], max_length=50)),
                ('enabled', models.BooleanField(default=False)),
                ('enabled_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('enabled_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enabled_addons', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addons', to='core.tenant')),
            ],
            options={
                'unique_together': {('tenant', 'addon_code')},
            },
        ),
    ]
