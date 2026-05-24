import requests

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_geo_location(ip):
    # For local testing, return default or use a public free API
    if not ip or ip == '127.0.0.1' or ip == 'localhost':
        return "Local City", "Localhost"
        
    try:
        # Timeout quickly to avoid blocking login flow
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('city', 'Unknown'), data.get('country', 'Unknown')
    except Exception:
        pass
        
    return "Unknown", "Unknown"
