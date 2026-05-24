import django.db.models.deletion
import uuid
from django.db import migrations, models


def seed_types_and_assign_employee_type(apps, schema_editor):
    EmployeeType = apps.get_model('employees', 'EmployeeType')
    Employee = apps.get_model('employees', 'Employee')
    Tenant = apps.get_model('core', 'Tenant')

    specs = [
        ('OFFICE', 'Office', False, True, False, 10, False, 200, True, False, False),
        ('FIELD', 'Field', True, True, True, 10, True, 200, False, True, True),
        ('REMOTE', 'Remote', False, False, False, 10, False, 200, False, True, False),
        ('HYBRID', 'Hybrid', False, True, False, 10, False, 200, True, False, False),
    ]
    for tenant in Tenant.objects.all():
        by_code = {}
        for code, name, req_selfie, req_gps, live, interval_m, block_home, radius, req_office, allow_remote, req_home in specs:
            obj, _ = EmployeeType.objects.get_or_create(
                tenant_id=tenant.id,
                code=code,
                defaults={
                    'name': name,
                    'is_active': True,
                    'require_selfie_on_punch': req_selfie,
                    'require_gps_on_punch': req_gps,
                    'enable_live_tracking': live,
                    'tracking_interval_minutes': interval_m,
                    'block_punch_near_home': block_home,
                    'home_exclusion_radius_meters': radius,
                    'require_office_geofence': req_office,
                    'allow_remote_punch': allow_remote,
                    'require_home_location': req_home,
                },
            )
            by_code[code] = obj
        office = by_code.get('OFFICE')
        if office:
            Employee.objects.filter(tenant_id=tenant.id, employee_type__isnull=True).update(employee_type=office)


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0004_widen_encrypted_pii_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('require_selfie_on_punch', models.BooleanField(default=False)),
                ('require_gps_on_punch', models.BooleanField(default=True)),
                ('enable_live_tracking', models.BooleanField(default=False)),
                ('tracking_interval_minutes', models.PositiveSmallIntegerField(default=10)),
                ('block_punch_near_home', models.BooleanField(default=False)),
                ('home_exclusion_radius_meters', models.PositiveIntegerField(default=200)),
                ('require_office_geofence', models.BooleanField(default=False)),
                ('allow_remote_punch', models.BooleanField(default=False)),
                ('require_home_location', models.BooleanField(default=False)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('tenant', 'code'), name='uniq_employee_type_tenant_code')],
            },
        ),
        migrations.AddField(
            model_name='employee',
            name='employee_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='employees.employeetype'),
        ),
        migrations.AddField(
            model_name='employee',
            name='office_location_verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='EmployeeWorkLocation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('home_address', models.TextField(blank=True, default='')),
                ('home_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('home_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='work_location', to='employees.employee')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.tenant')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RunPython(seed_types_and_assign_employee_type, migrations.RunPython.noop),
    ]
