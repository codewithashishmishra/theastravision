from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


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


@database_sync_to_async
def get_session_from_magic_token(session_id, magic_token):
    import uuid as uuid_mod

    from recruitment.models import AiInterviewSession

    try:
        token_uuid = uuid_mod.UUID(str(magic_token))
        return AiInterviewSession.objects.select_related('tenant').get(
            pk=session_id, magic_token=token_uuid
        )
    except (AiInterviewSession.DoesNotExist, ValueError, TypeError):
        return None


@database_sync_to_async
def session_allows_hr_watch(session_id, user):
    from recruitment.models import AiInterviewSession, TenantRecruitmentSettings

    if not user or not getattr(user, 'tenant_id', None):
        return False
    try:
        session = AiInterviewSession.objects.get(pk=session_id, tenant_id=user.tenant_id)
    except AiInterviewSession.DoesNotExist:
        return False
    settings = TenantRecruitmentSettings.get_for_tenant(session.tenant_id)
    return settings.live_watch_enabled


class InterviewLiveConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        query = self.scope.get('query_string', b'').decode()
        params = dict(p.split('=', 1) for p in query.split('&') if '=' in p)
        token = params.get('token', '')
        magic = params.get('magic_token', '')

        self.group = f'interview_session_{self.session_id}'
        self.role = None

        if token:
            self.user = await get_user_from_token(token)
            if not self.user:
                await self.close()
                return
            allowed = await session_allows_hr_watch(self.session_id, self.user)
            if not allowed:
                await self.close()
                return
            self.role = 'hr'
        elif magic:
            session = await get_session_from_magic_token(self.session_id, magic)
            if not session:
                await self.close()
                return
            self.role = 'candidate'
        else:
            await self.close()
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'role': self.role, 'session_id': self.session_id})

    async def disconnect(self, close_code):
        if hasattr(self, 'group'):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def transcript_segment(self, event):
        await self.send_json({
            'type': 'transcript_segment',
            'speaker': event.get('speaker'),
            'text': event.get('text'),
            'ts': event.get('ts'),
            'question_order': event.get('question_order'),
            'is_final': event.get('is_final', True),
        })

    async def session_state(self, event):
        await self.send_json({
            'type': 'session_state',
            'status': event.get('status'),
            'current_question_index': event.get('current_question_index'),
            'phase': event.get('phase'),
        })

    async def chunk_available(self, event):
        await self.send_json({
            'type': 'chunk_available',
            'kind': event.get('kind'),
            'sequence': event.get('sequence'),
            'byte_size': event.get('byte_size'),
            'created_at': event.get('created_at'),
        })

    async def concern_flagged(self, event):
        await self.send_json({
            'type': 'concern_flagged',
            'note': event.get('note'),
            'flagged_by': event.get('flagged_by'),
            'ts': event.get('ts'),
        })

    async def session_ended(self, event):
        await self.send_json({
            'type': 'session_ended',
            'status': event.get('status'),
            'ts': event.get('ts'),
        })
