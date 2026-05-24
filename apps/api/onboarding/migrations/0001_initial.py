import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnboardingChecklist',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='OnboardingTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255)),
                ('department', models.CharField(blank=True, default='', max_length=100)),
                ('sort_order', models.IntegerField(default=0)),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='onboarding.onboardingchecklist')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='OnboardingAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('progress', models.IntegerField(default=0)),
                ('status', models.CharField(default='In Progress', max_length=20)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='onboarding.onboardingchecklist')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='onboarding_assignments', to='employees.employee')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='BGVRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vendor', models.CharField(blank=True, default='', max_length=255)),
                ('status', models.CharField(default='Pending', max_length=20)),
                ('report_file', models.FileField(blank=True, null=True, upload_to='bgv_reports/')),
                ('notes', models.TextField(blank=True, default='')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bgv_records', to='employees.employee')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={'abstract': False},
        ),
    ]
