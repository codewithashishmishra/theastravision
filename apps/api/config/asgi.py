import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from notifications.routing import websocket_urlpatterns as notification_ws  # noqa: E402
from recruitment.routing import websocket_urlpatterns as interview_ws  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': URLRouter(notification_ws + interview_ws),
})
