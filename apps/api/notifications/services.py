from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from notifications.models import Notification


def notify_tenant_users(*, tenant_id, title, body='', category='general'):
    """Create in-app notifications for all active users in a tenant."""
    from core.models import User

    message = body or title
    for user in User.objects.filter(tenant_id=tenant_id, is_active=True).only('id'):
        notify_user(user.id, tenant_id, title, message, channel='In-App')


def notify_user(
    user_id,
    tenant_id,
    title,
    message,
    channel='In-App',
    *,
    category='general',
    link='',
    email_log_id=None,
):
    if not user_id:
        return None
    if tenant_id is None:
        from core.models import User

        user = User.objects.filter(pk=user_id).only('tenant_id').first()
        tenant_id = user.tenant_id if user else None
    if not tenant_id:
        return None
    n = Notification.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        title=title,
        message=message,
        channel=channel,
        category=category or Notification.CATEGORY_GENERAL,
        link=link or '',
        email_log_id=email_log_id,
    )
    payload = {
        'type': 'notification_message',
        'id': str(n.id),
        'title': n.title,
        'message': n.message,
        'is_read': n.is_read,
        'category': n.category,
        'link': n.link,
        'created_at': n.created_at.isoformat(),
    }
    layer = get_channel_layer()
    if layer:
        async_to_sync(layer.group_send)(f'user_{user_id}', payload)
    return n
