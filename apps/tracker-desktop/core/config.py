import os

API_BASE_URL = os.environ.get("AASTRAA_API_URL", "http://127.0.0.1:8000/api/v1")
# HRMS web login page (browser SSO for desktop tracker)
# Django-hosted login page (works without Next.js). Override to use admin-web if preferred.
WEB_LOGIN_URL = os.environ.get(
    "AASTRAA_WEB_LOGIN_URL", "http://127.0.0.1:8000/api/v1/tracker/auth/browser/"
)
