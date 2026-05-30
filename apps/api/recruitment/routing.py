from django.urls import re_path

from recruitment.consumers import InterviewLiveConsumer

websocket_urlpatterns = [
    re_path(
        r'ws/interviews/(?P<session_id>[0-9a-f-]+)/$',
        InterviewLiveConsumer.as_asgi(),
    ),
]
