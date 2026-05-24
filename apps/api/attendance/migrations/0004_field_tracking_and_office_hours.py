import django.db.models.deletion
import uuid
from django.db import migrations, models


def backfill_branch_coordinates_from_geofence(apps, schema_editor):
    Branch = apps.get_model('organization', 'Branch')
    GeoFence = apps.get_model('attendance', 'GeoFence')
    for branch in Branch.objects.all():
        if branch.latitude is not None and branch.longitude is not None:
            continue
        fence = GeoFence.objects.filter(branch_id=branch.id).first()
        if not fence:
            continue
        branch.latitude = fence.latitude
        branch.longitude = fence.longitude
        branch.geofence_radius_meters = fence.radius_meters or 50
        branch.save(update_fields=['latitude', 'longitude', 'geofence_radius_meters', 'updated_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0005_employee_type_tracking'),
        ('organization', '0005_branch_coordinates'),
        ('attendance', '0003_attendancelog_punch_source_attendancelog_selfie_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancesettings',
            name='office_hours_timezone',
            field=models.CharField(default='UTC', max_length=100),
        ),
        migrations.AddField(
            model_name='attendancesettings',
            name='work_days',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='attendancesettings',
            name='work_end_time',
            field=models.TimeField(default='18:00'),
        ),
        migrations.AddField(
            model_name='attendancesettings',
            name='work_start_time',
            field=models.TimeField(default='09:00'),
        ),
        migrations.CreateModel(
            name='FieldLocationPing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('accuracy_m', models.FloatField(blank=True, null=True)),
                ('source', models.CharField(choices=[('Web', 'Web'), ('Mobile', 'Mobile')], default='Web', max_length=20)),
                ('is_within_office_hours', models.BooleanField(default=True)),
                ('near_home', models.BooleanField(default=False)),
                ('attendance_log', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='field_pings', to='attendance.attendancelog')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='field_pings', to='employees.employee')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['tenant', 'employee', '-recorded_at'], name='att_fping_tenant_emp_idx'),
                    models.Index(fields=['tenant', 'recorded_at'], name='att_fping_tenant_rec_idx'),
                ],
            },
        ),
        migrations.RunPython(backfill_branch_coordinates_from_geofence, migrations.RunPython.noop),
    ]
