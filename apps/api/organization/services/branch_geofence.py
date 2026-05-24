"""Keep GeoFence in sync when branch coordinates are set."""

from attendance.models import GeoFence
from organization.models import Branch


def sync_branch_geofence(branch: Branch):
    if branch.latitude is None or branch.longitude is None:
        return
    GeoFence.objects.update_or_create(
        tenant_id=branch.tenant_id,
        branch=branch,
        defaults={
            'latitude': branch.latitude,
            'longitude': branch.longitude,
            'radius_meters': branch.geofence_radius_meters or 50,
        },
    )
