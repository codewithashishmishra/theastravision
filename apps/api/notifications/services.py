from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from notifications.models import Notification


def notify_user(user_id, tenant_id, title, message, channel='In-App'):
    if not user_id:
        return None
    n = Notification.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        title=title,
        message=message,
        channel=channel,
    )
    payload = {
        'type': 'notification_message',
        'id': str(n.id),
        'title': n.title,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat(),
    }
    layer = get_channel_layer()
    if layer:
        async_to_sync(layer.group_send)(f'user_{user_id}', payload)
    return n
