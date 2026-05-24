"""Seed default employee types per tenant."""

DEFAULT_TYPES = [
    {
        'code': 'OFFICE',
        'name': 'Office',
        'require_selfie_on_punch': False,
        'require_gps_on_punch': True,
        'enable_live_tracking': False,
        'tracking_interval_minutes': 10,
        'block_punch_near_home': False,
        'require_office_geofence': True,
        'allow_remote_punch': False,
        'require_home_location': False,
    },
    {
        'code': 'FIELD',
        'name': 'Field',
        'require_selfie_on_punch': True,
        'require_gps_on_punch': True,
        'enable_live_tracking': True,
        'tracking_interval_minutes': 10,
        'block_punch_near_home': True,
        'require_office_geofence': False,
        'allow_remote_punch': True,
        'require_home_location': True,
    },
    {
        'code': 'REMOTE',
        'name': 'Remote',
        'require_selfie_on_punch': False,
        'require_gps_on_punch': False,
        'enable_live_tracking': False,
        'tracking_interval_minutes': 10,
        'block_punch_near_home': False,
        'require_office_geofence': False,
        'allow_remote_punch': True,
        'require_home_location': False,
    },
    {
        'code': 'HYBRID',
        'name': 'Hybrid',
        'require_selfie_on_punch': False,
        'require_gps_on_punch': True,
        'enable_live_tracking': False,
        'tracking_interval_minutes': 10,
        'block_punch_near_home': False,
        'require_office_geofence': True,
        'allow_remote_punch': False,
        'require_home_location': False,
    },
]


def seed_employee_types_for_tenant(tenant_id):
    from employees.models import EmployeeType

    created = {}
    for spec in DEFAULT_TYPES:
        obj, _ = EmployeeType.objects.get_or_create(
            tenant_id=tenant_id,
            code=spec['code'],
            defaults={k: v for k, v in spec.items() if k not in ('code',)},
        )
        created[spec['code']] = obj
    return created


def assign_default_employee_type(employee):
    if employee.employee_type_id:
        return
    from employees.models import EmployeeType

    office = EmployeeType.objects.filter(tenant_id=employee.tenant_id, code='OFFICE').first()
    if office:
        employee.employee_type = office
        employee.save(update_fields=['employee_type', 'updated_at'])
