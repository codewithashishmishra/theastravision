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


def validate_punch_location(tenant_id, lat, lng):
    """Return (ok, message, distance_m, fence) for a punch at lat/lng."""
    if lat is None or lng is None:
        settings = AttendanceSettings.objects.filter(tenant_id=tenant_id).first()
        if settings and settings.require_gps:
            return False, 'GPS location is required for punch.', None, None
        return True, '', None, None

    fences = GeoFence.objects.filter(tenant_id=tenant_id).select_related('branch')
    if not fences.exists():
        settings = AttendanceSettings.objects.filter(tenant_id=tenant_id).first()
        default_radius = settings.default_radius_meters if settings else 50
        return True, '', 0, {'radius_meters': default_radius}

    settings = AttendanceSettings.objects.filter(tenant_id=tenant_id).first()
    best = None
    for fence in fences:
        dist = haversine_meters(lat, lng, fence.latitude, fence.longitude)
        radius = fence.radius_meters
        if settings and not fence.radius_meters:
            radius = settings.default_radius_meters
        if dist <= radius:
            return True, '', dist, fence
        if best is None or dist < best[0]:
            best = (dist, fence, radius)

    if best:
        dist, fence, radius = best
        return False, f'Outside office geofence ({int(dist)}m away, limit {radius}m).', dist, fence
    return False, 'No geofence configured for this location.', None, None
