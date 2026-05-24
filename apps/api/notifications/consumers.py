from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


@database_sync_to_async
def get_user_from_token(raw_token):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        token = AccessToken(raw_token)
        user_id = token.get('user_id')
        if not user_id:
            return None
        return User.objects.filter(id=user_id).first()
    except TokenError:
        return None


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        try:
            print("WS connect triggered")
            token = self.scope['query_string'].decode().split('token=')[-1].split('&')[0] if self.scope.get('query_string') else ''
            if not token:
                print("WS connect: No token")
                await self.close()
                return
            self.user = await get_user_from_token(token)
            if not self.user:
                print("WS connect: User not found for token")
                await self.close()
                return
            self.group = f'user_{self.user.id}'
            print(f"WS connect: Adding to group {self.group}")
            await self.channel_layer.group_add(self.group, self.channel_name)
            await self.accept()
            print("WS connect: Accepted")
        except Exception as e:
            print(f"WS connect EXCEPTION: {e}")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group'):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def notification_message(self, event):
        await self.send_json({
            'id': event.get('id'),
            'title': event.get('title'),
            'message': event.get('message'),
            'is_read': event.get('is_read', False),
            'created_at': event.get('created_at'),
        })
