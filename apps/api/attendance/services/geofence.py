import math
from decimal import Decimal

from attendance.models import AttendanceSettings, GeoFence


def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def validate_punch_location(tenant_id, lat, lng, *, require_gps=None, require_office_geofence=False, allow_remote_punch=False):
    """Return (ok, message, distance_m, fence) for a punch at lat/lng."""
    settings = AttendanceSettings.objects.filter(tenant_id=tenant_id).first()
    gps_required = require_gps if require_gps is not None else (settings.require_gps if settings else True)

    if lat is None or lng is None:
        if gps_required:
            return False, 'GPS location is required for punch.', None, None
        return True, '', None, None

    if allow_remote_punch and not require_office_geofence:
        return True, '', None, None

    fences = GeoFence.objects.filter(tenant_id=tenant_id).select_related('branch')
    if not fences.exists():
        if require_office_geofence:
            return False, 'Office geofence is not configured. Contact HR.', None, None
        default_radius = settings.default_radius_meters if settings else 50
        return True, '', 0, {'radius_meters': default_radius}

    best = None
    for fence in fences:
        dist = haversine_meters(lat, lng, fence.latitude, fence.longitude)
        radius = fence.radius_meters or (settings.default_radius_meters if settings else 50)
        if dist <= radius:
            return True, '', dist, fence
        if best is None or dist < best[0]:
            best = (dist, fence, radius)

    if best:
        dist, fence, radius = best
        if require_office_geofence:
            return False, f'Outside office geofence ({int(dist)}m away, limit {radius}m).', dist, fence
        return True, '', dist, fence
    if require_office_geofence:
        return False, 'No geofence configured for this location.', None, None
    return True, '', None, None
