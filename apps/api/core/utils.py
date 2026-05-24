import ipaddress

import requests

IP_GEO_API_TIMEOUT = 2


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _is_private_or_local_ip(ip: str | None) -> bool:
    if not ip or ip in ('127.0.0.1', 'localhost'):
        return True
    try:
        addr = ipaddress.ip_address(ip.strip())
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        return True


def fetch_ip_geo(ip: str | None) -> dict | None:
    """Fetch city, country, and timezone from ip-api.com. Returns None for local/private IPs."""
    if _is_private_or_local_ip(ip):
        return None

    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=IP_GEO_API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'city': data.get('city', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'timezone': data.get('timezone'),
                }
    except Exception:
        pass

    return None


def get_geo_location(ip):
    if _is_private_or_local_ip(ip):
        return "Local City", "Localhost"

    geo = fetch_ip_geo(ip)
    if geo:
        return geo.get('city', 'Unknown'), geo.get('country', 'Unknown')

    return "Unknown", "Unknown"
