import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets  # noqa: F401 - viewsets used by AssessmentPublicViewSet
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from organization.views import BaseTenantViewSet
from recruitment.document_parser import validate_upload_filename
import base64

from recruitment.interview_storage import InterviewStorageService
from recruitment.conversation import ConversationManager
from recruitment.astra_tts_storage import persist_astra_tts
from recruitment.live_auth import get_session_for_magic_token
from recruitment.live_events import (
    emit_chunk_available,
    emit_concern_flagged,
    emit_session_ended,
    emit_session_state,
    emit_transcript_segment,
)
from recruitment.models import (
    AiInterviewBugReport,
    AiInterviewMediaBlob,
    AiInterviewMediaChunk,
    AiInterviewQuestion,
    AiInterviewReport,
    AiInterviewSession,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentTemplate,
    Candidate,
    Interview,
    JobRequisition,
    ProctorSnapshot,
    TenantRecruitmentSettings,
)
from recruitment.serializers import (
    AiInterviewBugReportSerializer,
    AiInterviewQuestionPublicSerializer,
    AiInterviewQuestionSerializer,
    AiInterviewReportSerializer,
    AiInterviewSessionPublicSerializer,
    AiInterviewSessionSerializer,
    AssessmentQuestionPublicSerializer,
    AssessmentQuestionSerializer,
    AssessmentTemplateSerializer,
    AssessmentAttemptSerializer,
    CandidateSerializer,
    InterviewSerializer,
    JobRequisitionSerializer,
    ProctorSnapshotSerializer,
)
from recruitment.career_portal_views import JobRequisitionCareerMixin
from recruitment.services import (
    SKIP_LIMIT,
    complete_voice_interview,
    count_skipped_questions,
    create_ai_session,
    ensure_assessment_template,
    ensure_questions,
    extract_text_from_file,
    get_magic_link,
    process_voice_answer,
    run_candidate_match,
    score_assessment_attempt,
    skip_voice_question,
)
from recruitment.tasks import generate_and_email_report, send_interview_invite_email


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class JobRequisitionViewSet(JobRequisitionCareerMixin, BaseTenantViewSet):
    queryset = JobRequisition.objects.all()
    serializer_class = JobRequisitionSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = super().get_queryset()
        published = self.request.query_params.get('published')
        if published == 'true':
            qs = qs.filter(is_published=True)
        elif published == 'false':
            qs = qs.filter(is_published=False)
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def perform_create(self, serializer):
        from recruitment.models import JobRequisition
        from recruitment.tasks import parse_job_jd_task

        tenant_id = getattr(self.request, 'tenant_id', None)
        jd = self.request.FILES.get('jd_file')
        if jd:
            try:
                validate_upload_filename(jd.name)
            except DjangoValidationError as exc:
                raise ValidationError({'jd_file': str(exc)}) from exc
        instance = serializer.save(tenant_id=tenant_id)
        if jd:
            instance.jd_parse_status = JobRequisition.PARSE_PROCESSING
            instance.save(update_fields=['jd_parse_status', 'updated_at'])
            parse_job_jd_task.delay(str(instance.id))

    def perform_update(self, serializer):
        from recruitment.models import JobRequisition
        from recruitment.tasks import parse_job_jd_task

        jd = self.request.FILES.get('jd_file')
        if jd:
            try:
                validate_upload_filename(jd.name)
            except DjangoValidationError as exc:
                raise ValidationError({'jd_file': str(exc)}) from exc
        instance = serializer.save()
        if jd:
            instance.jd_parse_status = JobRequisition.PARSE_PROCESSING
            instance.save(update_fields=['jd_parse_status', 'updated_at'])
            parse_job_jd_task.delay(str(instance.id))

    @action(detail=True, methods=['get'], url_path='parse-status')
    def parse_status(self, request, pk=None):
        job = self.get_object()
        return Response({
            'jd_parse_status': job.jd_parse_status,
            'jd_parse_error': job.jd_parse_error,
        })


class CandidateViewSet(BaseTenantViewSet):
    queryset = Candidate.objects.select_related(
        'job', 'proposed_reporting_manager', 'campaign'
    ).prefetch_related('ai_sessions').all()
    serializer_class = CandidateSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = super().get_queryset()
        campaign_id = self.request.query_params.get('campaign')
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        return qs

    def get_serializer_context(self):
        from core.tenant_utils import resolve_request_tenant_id

        ctx = super().get_serializer_context()
        ctx['tenant_id'] = resolve_request_tenant_id(self.request)
        return ctx

    def perform_create(self, serializer):
        from recruitment.models import JobRequisition
        from recruitment.tasks import parse_resume_and_match_task

        tenant_id = getattr(self.request, 'tenant_id', None)
        resume = self.request.FILES.get('resume_file')
        if resume:
            try:
                validate_upload_filename(resume.name)
            except DjangoValidationError as exc:
                raise ValidationError({'resume_file': str(exc)}) from exc
        instance = serializer.save(tenant_id=tenant_id)
        if resume:
            instance.resume_parse_status = JobRequisition.PARSE_PROCESSING
            instance.save(update_fields=['resume_parse_status', 'updated_at'])
            parse_resume_and_match_task.delay(str(instance.id))

    @action(detail=True, methods=['get'], url_path='parse-status')
    def parse_status(self, request, pk=None):
        candidate = self.get_object()
        threshold = candidate.job.match_threshold or 70
        return Response({
            'resume_parse_status': candidate.resume_parse_status,
            'resume_parse_error': candidate.resume_parse_error,
            'ai_match_score': candidate.ai_match_score,
            'match_passed': candidate.ai_match_score >= threshold,
            'threshold': threshold,
            'match_breakdown': candidate.match_breakdown,
        })

    @action(detail=True, methods=['post'])
    def match(self, request, pk=None):
        candidate = self.get_object()
        try:
            data = run_candidate_match(candidate)
            threshold = candidate.job.match_threshold or 70
            return Response({
                'status': 'success',
                'ai_analysis': data,
                'new_score': candidate.ai_match_score,
                'match_passed': candidate.ai_match_score >= threshold,
                'threshold': threshold,
            })
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        from django.utils.dateparse import parse_datetime

        candidate = self.get_object()
        threshold = candidate.job.match_threshold or 70
        force = bool(request.data.get('force', False))
        if candidate.ai_sessions.exists():
            return Response(
                {'error': 'An interview has already been scheduled for this candidate.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not force and candidate.ai_match_score < threshold:
            return Response(
                {'error': f'Match score {candidate.ai_match_score}% is below threshold {threshold}%.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        expiry_minutes = int(request.data.get('expiry_minutes', 120))
        expiry_minutes = max(15, min(10080, expiry_minutes))
        include_assessment = bool(request.data.get('include_assessment', False))
        session = create_ai_session(
            candidate,
            expiry_minutes=expiry_minutes,
            include_assessment=include_assessment,
        )
        flags = dict(session.proctor_flags or {})
        scheduled_raw = request.data.get('scheduled_at')
        scheduled_dt = None
        if scheduled_raw:
            scheduled_dt = parse_datetime(str(scheduled_raw))
            if scheduled_dt:
                if timezone.is_naive(scheduled_dt):
                    scheduled_dt = timezone.make_aware(scheduled_dt)
                flags['scheduled_at'] = scheduled_dt.isoformat()
        tz_raw = request.data.get('scheduled_timezone')
        if tz_raw:
            flags['scheduled_timezone'] = str(tz_raw)
        cc_emails = list(request.data.get('cc_emails') or [])
        if request.data.get('cc_hr_admin') and request.user.email:
            if request.user.email not in cc_emails:
                cc_emails.append(request.user.email)
        if cc_emails:
            flags['cc_emails'] = cc_emails
        if flags:
            session.proctor_flags = flags
            session.save(update_fields=['proctor_flags'])
        send_email = request.data.get('send_email', candidate.job.auto_send_invite)
        if send_email:
            from recruitment.tasks import schedule_interview_invite_email

            schedule_interview_invite_email(str(session.id), scheduled_dt)
        return Response({
            'status': 'success',
            'session_id': str(session.id),
            'magic_link': get_magic_link(session),
            'expires_at': session.expires_at,
            'scheduled_at': flags.get('scheduled_at'),
        })


class InterviewViewSet(BaseTenantViewSet):
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer

    @action(detail=True, methods=['post'])
    def generate_magic_link(self, request, pk=None):
        interview = self.get_object()
        expiry_minutes = int(request.data.get('expiry_minutes', 30))
        expiry_minutes = max(15, min(120, expiry_minutes))
        interview.magic_token = uuid.uuid4()
        interview.token_expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        interview.save()
        from django.conf import settings
        frontend_base = getattr(settings, 'FRONTEND_APP_URL', 'http://localhost:3000').rstrip('/')
        magic_link = f"{frontend_base}/interview/join/{interview.magic_token}"
        return Response({
            'status': 'success',
            'magic_link': magic_link,
            'expires_at': interview.token_expires_at,
        })

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='verify-link/(?P<token>[^/.]+)')
    def verify_magic_link(self, request, token=None):
        try:
            interview = Interview.objects.get(magic_token=token)
            if not interview.token_expires_at or timezone.now() > interview.token_expires_at:
                return Response({'error': 'This interview link has expired.'}, status=status.HTTP_403_FORBIDDEN)
            return Response({
                'status': 'valid',
                'candidate_name': interview.candidate.first_name,
                'job_title': interview.candidate.job.title,
                'scheduled_at': interview.scheduled_at,
                'duration_minutes': interview.duration_minutes,
            })
        except Interview.DoesNotExist:
            return Response({'error': 'Interview not found.'}, status=status.HTTP_404_NOT_FOUND)


class AiInterviewSessionViewSet(BaseTenantViewSet):
    queryset = AiInterviewSession.objects.select_related('candidate', 'job').select_related('report').all()
    serializer_class = AiInterviewSessionSerializer

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='verify/(?P<token>[^/.]+)')
    def verify(self, request, token=None):
        try:
            session = AiInterviewSession.objects.select_related('candidate', 'job').get(magic_token=token)
            if session.status in ('completed', 'failed', 'expired'):
                return Response(
                    {'error': 'This interview has already been completed or is no longer available.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if session.expires_at and timezone.now() > session.expires_at:
                session.status = 'expired'
                session.save(update_fields=['status'])
                return Response({'error': 'Link expired.'}, status=status.HTTP_403_FORBIDDEN)
            return Response(AiInterviewSessionPublicSerializer(session).data)
        except AiInterviewSession.DoesNotExist:
            return Response({'error': 'Invalid link.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], url_path='start')
    def start(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        if session.expires_at and timezone.now() > session.expires_at:
            return Response({'error': 'Session expired.'}, status=status.HTTP_403_FORBIDDEN)
        session.consent_at = timezone.now()
        session.consent_ip = _client_ip(request)
        session.status = 'active'
        session.save(update_fields=['consent_at', 'consent_ip', 'status'])
        ensure_questions(session)
        return Response({'status': 'active', 'question_count': session.questions.count()})

    @action(detail=True, methods=['get'], permission_classes=[AllowAny], url_path='questions/next')
    def next_question(self, request, pk=None):
        session = AiInterviewSession.objects.prefetch_related('questions').get(pk=pk)
        conversation = ConversationManager()
        envelope = conversation.start_turn(str(session.id))
        if not envelope:
            return Response({'done': True})
        qs = envelope.question
        audio_b64 = None
        tts_mime = envelope.tts_mime
        tts_attempts = 0
        tts_meta = {}
        try:
            audio_bytes = envelope.tts_audio
            if audio_bytes:
                tts_meta = persist_astra_tts(session, audio_bytes, sequence=qs.order)
                audio_b64 = base64.b64encode(audio_bytes).decode('ascii')
            else:
                tts_attempts = 1
        except Exception:
            audio_b64 = None
        skip_count = count_skipped_questions(session)
        return Response({
            'done': False,
            'question': {
                **AiInterviewQuestionPublicSerializer(qs).data,
                'question_text': envelope.ask_text,
            },
            'index': qs.order,
            'total': session.questions.count(),
            'tts_audio_base64': audio_b64,
            'tts_mime': tts_mime,
            'tts_available': audio_b64 is not None,
            'tts_attempts': tts_attempts,
            'tts_voice': 'xyz-kokoro82m',
            'tts_sequence': tts_meta.get('sequence'),
            'tts_filename': tts_meta.get('filename'),
            'skip_count': skip_count,
            'skip_limit': SKIP_LIMIT,
            'silence_timeout_seconds': conversation.silence_timeout_seconds,
            'timeout_prompt': 'Would you like to skip this question, or should I repeat it?',
            'include_assessment': bool(session.include_assessment),
        })

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], url_path='turn-decision')
    def turn_decision(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        question_id = request.data.get('question_id')
        candidate_reply = (request.data.get('decision') or '').strip()
        if not question_id:
            return Response({'error': 'question_id required.'}, status=status.HTTP_400_BAD_REQUEST)
        question = AiInterviewQuestion.objects.get(pk=question_id, session=session)
        conversation = ConversationManager()
        decision = conversation.resolve_repeat_skip(candidate_reply)
        if decision == 'repeat':
            return Response({'ok': True, 'action': 'repeat'})
        if decision == 'skip':
            result = skip_voice_question(session, question)
            return Response({'ok': True, 'action': 'skip', **result})
        return Response({'ok': True, 'action': 'continue'})

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], parser_classes=[MultiPartParser])
    def answers(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        question_id = request.data.get('question_id')
        audio = request.FILES.get('audio')
        if not question_id or not audio:
            return Response({'error': 'question_id and audio required.'}, status=status.HTTP_400_BAD_REQUEST)
        question = AiInterviewQuestion.objects.get(pk=question_id, session=session)
        try:
            process_voice_answer(session, question, audio)
            session.current_question_index = question.order
            session.save(update_fields=['current_question_index'])
            return Response({'ok': True, 'question_id': str(question.id)})
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], url_path='questions/skip')
    def skip_question(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        question_id = request.data.get('question_id')
        if not question_id:
            return Response({'error': 'question_id required.'}, status=status.HTTP_400_BAD_REQUEST)
        question = AiInterviewQuestion.objects.get(pk=question_id, session=session)
        result = skip_voice_question(session, question)
        return Response({'ok': True, 'skipped': True, **result})

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], url_path='speak')
    def speak(self, request, pk=None):
        import logging

        logger = logging.getLogger(__name__)
        session = AiInterviewSession.objects.get(pk=pk)
        text = (request.data.get('text') or '').strip()
        if not text:
            return Response({'error': 'text required.'}, status=status.HTTP_400_BAD_REQUEST)
        utterance_hint = request.data.get('utterance_index')
        preferred_seq = int(utterance_hint) if utterance_hint is not None else None
        audio_b64 = None
        tts_mime = 'audio/mpeg'
        tts_attempts = 0
        tts_meta = {}
        conversation = ConversationManager()
        try:
            audio_bytes, tts_mime = conversation.stream_question_tts(text)
            tts_attempts = 1
            if not audio_bytes:
                raise ValueError('TTS returned no audio bytes')
            tts_meta = persist_astra_tts(session, audio_bytes, sequence=preferred_seq)
            audio_b64 = base64.b64encode(audio_bytes).decode('ascii')
        except Exception as exc:
            logger.exception('speak TTS failed session=%s', session.id)
            return Response(
                {
                    'error': str(exc),
                    'tts_available': False,
                    'tts_attempts': tts_attempts,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        emit_transcript_segment(session.id, speaker='AI', text=text, is_final=True)
        return Response({
            'tts_audio_base64': audio_b64,
            'tts_mime': tts_mime,
            'tts_available': True,
            'tts_attempts': tts_attempts,
            'tts_voice': 'xyz-kokoro82m',
            'tts_sequence': tts_meta.get('sequence'),
            'tts_filename': tts_meta.get('filename'),
        })

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], url_path='preflight')
    def preflight(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        flags = dict(session.proctor_flags or {})
        flags['preflight_completed_at'] = timezone.now().isoformat()
        flags['tab_switch_count'] = int(flags.get('tab_switch_count') or 0)
        session.proctor_flags = flags
        session.save(update_fields=['proctor_flags', 'updated_at'])
        return Response({'ok': True})

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], url_path='feedback')
    def feedback(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        rating = request.data.get('rating')
        comment = (request.data.get('comment') or '').strip()[:2000]
        session.candidate_feedback = {
            'rating': rating,
            'comment': comment,
            'submitted_at': timezone.now().isoformat(),
        }
        session.save(update_fields=['candidate_feedback', 'updated_at'])
        return Response({'ok': True})

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
        url_path='upload-recording',
        parser_classes=[MultiPartParser],
    )
    def upload_recording(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        if session.session_recording_path and session.session_recording_path.startswith('blob:'):
            return Response({'ok': True, 'skipped': 'already_finalized'})
        session_video = request.FILES.get('session_video')
        camera_video = request.FILES.get('camera_video')
        if InterviewStorageService.use_pg_blobs():
            if session_video:
                data = session_video.read()
                blob = InterviewStorageService.save_blob(
                    session,
                    AiInterviewMediaBlob.KIND_SESSION_COMPOSITE,
                    data,
                    content_type='video/webm',
                )
                session.session_recording_path = f'blob:{blob.id}'
            if camera_video:
                data_cam = camera_video.read()
                blob_cam = InterviewStorageService.save_blob(
                    session,
                    AiInterviewMediaBlob.KIND_CAMERA,
                    data_cam,
                    content_type='video/webm',
                )
                session.camera_recording_path = f'blob:{blob_cam.id}'
        else:
            if session_video:
                rel = f"interviews/{session.tenant_id}/{session.id}/session.webm"
                session.session_recording_path = InterviewStorageService.save_upload(rel, session_video)
            if camera_video:
                rel_cam = f"interviews/{session.tenant_id}/{session.id}/camera.webm"
                session.camera_recording_path = InterviewStorageService.save_upload(rel_cam, camera_video)
        if request.data.get('recording_started_at'):
            from django.utils.dateparse import parse_datetime

            started = parse_datetime(str(request.data['recording_started_at']))
            if started:
                session.recording_started_at = started
        session.recording_ended_at = timezone.now()
        tab_switches = request.data.get('tab_switch_count')
        if tab_switches is not None:
            flags = dict(session.proctor_flags or {})
            flags['tab_switch_count'] = int(tab_switches)
            session.proctor_flags = flags
        session.save(
            update_fields=[
                'session_recording_path',
                'camera_recording_path',
                'recording_started_at',
                'recording_ended_at',
                'proctor_flags',
                'updated_at',
            ]
        )
        return Response({'ok': True})

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], url_path='complete-voice')
    def complete_voice(self, request, pk=None):
        from recruitment.tasks import async_background_report_generation

        session = AiInterviewSession.objects.get(pk=pk)
        complete_voice_interview(session)
        if session.status in ('completed', 'failed'):
            async_background_report_generation.apply_async(args=[str(session.id)], countdown=30 * 60)
        assessment_link = None
        if session.status == 'voice_passed' and session.include_assessment:
            assessment_link = f"/assessment/{session.magic_token}"
        return Response({'status': session.status, 'assessment_link': assessment_link})

    @action(detail=True, methods=['get'], url_path='live')
    def live(self, request, pk=None):
        session = self.get_object()
        settings = TenantRecruitmentSettings.get_for_tenant(session.tenant_id)
        current_q = session.questions.filter(answered_at__isnull=True).order_by('order').first()
        return Response({
            'id': str(session.id),
            'status': session.status,
            'candidate_name': f'{session.candidate.first_name} {session.candidate.last_name}',
            'candidate_avatar': getattr(session.candidate, 'profile_picture', None) or '',
            'job_title': session.job.title,
            'current_question_index': session.current_question_index,
            'current_question_text': current_q.question_text if current_q else None,
            'recording_started_at': session.recording_started_at,
            'recording_ended_at': session.recording_ended_at,
            'live_watch_enabled': settings.live_watch_enabled,
            'proctor_flags': session.proctor_flags or {},
            'question_count': session.questions.count(),
        })

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
        url_path='live/chunks',
        parser_classes=[MultiPartParser],
    )
    def live_chunks(self, request, pk=None):
        session = get_session_for_magic_token(pk, request)
        kind = request.data.get('kind') or AiInterviewMediaChunk.KIND_SESSION_COMPOSITE
        if kind not in (AiInterviewMediaChunk.KIND_SESSION_COMPOSITE, AiInterviewMediaChunk.KIND_CAMERA):
            return Response({'error': 'Invalid kind.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            sequence = int(request.data.get('sequence', 0))
        except (TypeError, ValueError):
            return Response({'error': 'sequence required.'}, status=status.HTTP_400_BAD_REQUEST)
        chunk_file = request.FILES.get('chunk')
        if not chunk_file:
            return Response({'error': 'chunk file required.'}, status=status.HTTP_400_BAD_REQUEST)
        data = chunk_file.read()
        if len(data) > 2 * 1024 * 1024:
            return Response({'error': 'Chunk too large (max 2MB).'}, status=status.HTTP_400_BAD_REQUEST)
        content_type = chunk_file.content_type or 'video/webm'
        chunk = InterviewStorageService.save_chunk(
            session, kind, sequence, data, content_type=content_type
        )
        if not session.recording_started_at:
            session.recording_started_at = timezone.now()
            session.save(update_fields=['recording_started_at', 'updated_at'])
        emit_chunk_available(
            session.id,
            kind=kind,
            sequence=sequence,
            byte_size=chunk.byte_size,
            created_at=chunk.created_at.isoformat(),
        )
        return Response({'ok': True, 'sequence': sequence, 'kind': kind})

    @action(detail=True, methods=['get'], url_path='live/chunks/list')
    def live_chunks_list(self, request, pk=None):
        session = self.get_object()
        kind = request.query_params.get('kind')
        since = int(request.query_params.get('since', 0))
        chunks = InterviewStorageService.list_chunks(session.id, kind=kind or None, since_sequence=since)
        return Response({
            'chunks': [
                {
                    'kind': c.kind,
                    'sequence': c.sequence,
                    'byte_size': c.byte_size,
                    'content_type': c.content_type,
                    'created_at': c.created_at.isoformat(),
                }
                for c in chunks
            ],
        })

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
        url_path='live/finalize-recording',
    )
    def live_finalize_recording(self, request, pk=None):
        session = get_session_for_magic_token(pk, request)
        merged = InterviewStorageService.finalize_session_recordings(session)
        session.recording_ended_at = timezone.now()
        tab_switches = request.data.get('tab_switch_count')
        if tab_switches is not None:
            flags = dict(session.proctor_flags or {})
            flags['tab_switch_count'] = int(tab_switches)
            session.proctor_flags = flags
        session.save(
            update_fields=[
                'session_recording_path',
                'camera_recording_path',
                'recording_ended_at',
                'proctor_flags',
                'updated_at',
            ]
        )
        emit_session_state(session.id, status=session.status, phase='recording_finalized')
        return Response({'ok': True, 'blobs': merged})

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
        url_path='bug-report',
        parser_classes=[MultiPartParser, FormParser],
    )
    def bug_report(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        title = (request.data.get('title') or '').strip()
        description = (request.data.get('description') or '').strip()
        image = request.FILES.get('image')
        if not title:
            return Response({'error': 'title is required.'}, status=status.HTTP_400_BAD_REQUEST)

        report = AiInterviewBugReport.objects.create(
            tenant_id=session.tenant_id,
            session=session,
            title=title[:200],
            description=description[:4000],
            image=image,
        )
        return Response(
            AiInterviewBugReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='terminate')
    def terminate(self, request, pk=None):
        session = self.get_object()
        if session.status not in ('active', 'pending', 'assessment', 'voice_passed'):
            return Response({'error': 'Session cannot be terminated.'}, status=status.HTTP_400_BAD_REQUEST)
        session.status = 'failed'
        flags = dict(session.proctor_flags or {})
        flags['terminated_by_hr'] = True
        flags['terminated_at'] = timezone.now().isoformat()
        session.proctor_flags = flags
        session.save(update_fields=['status', 'proctor_flags', 'updated_at'])
        emit_session_ended(str(session.id), status=session.status)
        return Response({'ok': True, 'status': session.status})

    @action(detail=True, methods=['post'], url_path='flag-concern')
    def flag_concern(self, request, pk=None):
        session = self.get_object()
        note = (request.data.get('note') or request.data.get('reason') or 'Concern flagged by HR').strip()[:2000]
        flags = dict(session.proctor_flags or {})
        concerns = list(flags.get('concerns') or [])
        concerns.append({
            'note': note,
            'at': timezone.now().isoformat(),
            'by': str(getattr(request.user, 'id', '')),
        })
        flags['concerns'] = concerns
        session.proctor_flags = flags
        session.save(update_fields=['proctor_flags', 'updated_at'])
        emit_concern_flagged(session.id, note=note, flagged_by=str(getattr(request.user, 'email', '')))
        return Response({'ok': True})


class AssessmentTemplateViewSet(BaseTenantViewSet):
    queryset = AssessmentTemplate.objects.prefetch_related('questions').all()
    serializer_class = AssessmentTemplateSerializer

    @action(detail=True, methods=['post'], url_path='generate')
    def generate(self, request, pk=None):
        template = self.get_object()
        job = template.job
        from recruitment.ai_client import ai_post
        result = ai_post('/api/v1/ai/generate-assessment', {
            'job_title': job.title,
            'job_description': job.description,
            'resume_text': '',
            'count': template.question_count,
        })
        template.questions.all().delete()
        for idx, q in enumerate(result.get('questions', []), start=1):
            opts = q.get('options', {})
            AssessmentQuestion.objects.create(
                tenant_id=template.tenant_id,
                template=template,
                order=idx,
                prompt=q.get('prompt', ''),
                option_a=opts.get('A', ''),
                option_b=opts.get('B', ''),
                option_c=opts.get('C', ''),
                option_d=opts.get('D', ''),
                correct_option=q.get('correct_option', 'A'),
            )
        return Response(AssessmentTemplateSerializer(template).data)


class AssessmentPublicViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _session_from_token(self, token):
        return AiInterviewSession.objects.select_related('job', 'candidate').get(
            magic_token=token, status__in=['voice_passed', 'assessment', 'completed']
        )

    def retrieve_assessment(self, request, token=None):
        try:
            session = self._session_from_token(token)
        except AiInterviewSession.DoesNotExist:
            return Response({'error': 'Assessment not available.'}, status=status.HTTP_404_NOT_FOUND)
        if not session.include_assessment:
            return Response({'error': 'Assessment was not included for this interview.'}, status=status.HTTP_400_BAD_REQUEST)
        template = ensure_assessment_template(session)
        attempt, _ = AssessmentAttempt.objects.get_or_create(
            tenant_id=session.tenant_id,
            session=session,
            defaults={},
        )
        return Response({
            'session_id': str(session.id),
            'duration_minutes': template.duration_minutes,
            'proctor_interval_seconds': template.proctor_interval_seconds,
            'questions': AssessmentQuestionPublicSerializer(template.questions.all(), many=True).data,
            'started_at': attempt.started_at,
        })

    def start_assessment(self, request, token=None):
        session = self._session_from_token(token)
        attempt, _ = AssessmentAttempt.objects.get_or_create(tenant_id=session.tenant_id, session=session)
        if not attempt.started_at:
            attempt.started_at = timezone.now()
        attempt.camera_active = bool(request.data.get('camera_active'))
        attempt.save()
        session.status = 'assessment'
        session.save(update_fields=['status'])
        return Response(AssessmentAttemptSerializer(attempt).data)

    def submit(self, request, token=None):
        session = self._session_from_token(token)
        attempt = AssessmentAttempt.objects.get(session=session)
        if not attempt.camera_active:
            return Response({'error': 'Camera must remain on during the exam.'}, status=status.HTTP_400_BAD_REQUEST)
        attempt.answers = request.data.get('answers', {})
        attempt.save(update_fields=['answers'])
        score = score_assessment_attempt(attempt)
        return Response({'score': score, 'status': session.status})

    def proctor_snapshot(self, request, token=None):
        session = self._session_from_token(token)
        attempt = AssessmentAttempt.objects.get(session=session)
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'image required'}, status=status.HTTP_400_BAD_REQUEST)
        rel = f"interviews/{session.tenant_id}/{session.id}/proctor/{uuid.uuid4()}.jpg"
        path = InterviewStorageService.save_upload(rel, image)
        snap = ProctorSnapshot.objects.create(
            tenant_id=session.tenant_id,
            attempt=attempt,
            image_path=path,
        )
        return Response(ProctorSnapshotSerializer(snap).data)


class AiInterviewReportViewSet(BaseTenantViewSet):
    queryset = AiInterviewReport.objects.select_related('session__candidate', 'session__job').all()
    serializer_class = AiInterviewReportSerializer

    def retrieve(self, request, *args, **kwargs):
        from django.conf import settings

        report = self.get_object()
        data = AiInterviewReportSerializer(report).data
        session = report.session
        api_base = request.build_absolute_uri('/').rstrip('/')
        recruitment_base = f'{api_base}/api/v1/recruitment'

        def _blob_media_url(kind: str, question_order: int | None = None) -> str | None:
            blob = InterviewStorageService.get_blob(session.id, kind, question_order=question_order)
            if blob:
                url = f'{recruitment_base}/ai-sessions/{session.id}/media/{kind}/'
                if question_order is not None:
                    url += f'?question_order={question_order}'
                return url
            return None

        def _media_url(path: str, kind: str, question_order: int | None = None) -> str | None:
            if not path:
                return _blob_media_url(kind, question_order)
            if path.startswith('blob:'):
                return f'{recruitment_base}/ai-sessions/{session.id}/media/{kind}/' + (
                    f'?question_order={question_order}' if question_order else ''
                )
            media_base = getattr(settings, 'PUBLIC_API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
            return f'{media_base}/media/{path.lstrip("/")}'

        questions_payload = []
        for q in session.questions.all().order_by('order'):
            q_data = AiInterviewQuestionSerializer(q).data
            q_data['audio_url'] = _media_url(
                q.audio_path, AiInterviewMediaBlob.KIND_ANSWER_AUDIO, question_order=q.order
            )
            q_data['skipped'] = q.skipped
            questions_payload.append(q_data)
        data['questions'] = questions_payload
        data['session_recording_url'] = _media_url(
            session.session_recording_path, AiInterviewMediaBlob.KIND_SESSION_COMPOSITE
        )
        data['camera_recording_url'] = _media_url(
            session.camera_recording_path, AiInterviewMediaBlob.KIND_CAMERA
        )
        data['proctor_flags'] = session.proctor_flags or {}
        data['candidate_feedback'] = session.candidate_feedback or {}
        attempt = getattr(session, 'assessment_attempt', None)
        if attempt:
            data['proctor_snapshots'] = [
                {
                    'id': str(s.id),
                    'captured_at': s.captured_at,
                    'image_path': s.image_path,
                    'image_url': _media_url(s.image_path),
                }
                for s in attempt.snapshots.all()[:50]
            ]
        return Response(data)
