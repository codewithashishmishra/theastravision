"""Merge tenant AttendanceSettings with EmployeeType rules for punch validation."""

from dataclasses import dataclass
from typing import Optional

from attendance.models import AttendanceSettings
from employees.models import Employee, EmployeeWorkLocation


@dataclass
class AttendanceRuleSnapshot:
    require_selfie: bool
    require_gps: bool
    enable_live_tracking: bool
    tracking_interval_minutes: int
    block_punch_near_home: bool
    home_exclusion_radius_meters: int
    require_office_geofence: bool
    allow_remote_punch: bool
    require_home_location: bool


def resolve_attendance_rules(employee: Employee) -> AttendanceRuleSnapshot:
    settings = AttendanceSettings.objects.filter(tenant_id=employee.tenant_id).first()
    et = getattr(employee, 'employee_type', None)
    if et is None and employee.employee_type_id:
        from employees.models import EmployeeType
        et = EmployeeType.objects.filter(pk=employee.employee_type_id).first()

    tenant_selfie = settings.require_selfie if settings else False
    tenant_gps = settings.require_gps if settings else True

    if et:
        return AttendanceRuleSnapshot(
            require_selfie=tenant_selfie or et.require_selfie_on_punch,
            require_gps=tenant_gps or et.require_gps_on_punch,
            enable_live_tracking=et.enable_live_tracking,
            tracking_interval_minutes=max(5, min(15, et.tracking_interval_minutes)),
            block_punch_near_home=et.block_punch_near_home,
            home_exclusion_radius_meters=et.home_exclusion_radius_meters,
            require_office_geofence=et.require_office_geofence,
            allow_remote_punch=et.allow_remote_punch,
            require_home_location=et.require_home_location,
        )

    return AttendanceRuleSnapshot(
        require_selfie=tenant_selfie,
        require_gps=tenant_gps,
        enable_live_tracking=False,
        tracking_interval_minutes=10,
        block_punch_near_home=False,
        home_exclusion_radius_meters=200,
        require_office_geofence=False,
        allow_remote_punch=False,
        require_home_location=False,
    )


def employee_home_location_complete(employee: Employee) -> bool:
    try:
        wl = employee.work_location
    except EmployeeWorkLocation.DoesNotExist:
        return False
    return wl.has_home_coordinates()


def validate_not_near_home(employee: Employee, lat, lng, rules: AttendanceRuleSnapshot) -> tuple[bool, str]:
    if not rules.block_punch_near_home or lat is None or lng is None:
        return True, ''
    try:
        wl = employee.work_location
    except EmployeeWorkLocation.DoesNotExist:
        return True, ''

    if not wl.has_home_coordinates():
        return True, ''

    from attendance.services.geofence import haversine_meters

    dist = haversine_meters(lat, lng, wl.home_latitude, wl.home_longitude)
    if dist <= rules.home_exclusion_radius_meters:
        return False, (
            f'Punch blocked: you are within {int(dist)}m of your registered home '
            f'(limit {rules.home_exclusion_radius_meters}m). Field staff must punch from the field.'
        )
    return True, ''
