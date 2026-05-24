import uuid
from datetime import timedelta

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
from recruitment.ai_client import ai_get_bytes
from recruitment.interview_storage import InterviewStorageService
from recruitment.models import (
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
)
from recruitment.serializers import (
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
    complete_voice_interview,
    create_ai_session,
    ensure_assessment_template,
    ensure_questions,
    extract_text_from_file,
    get_magic_link,
    process_voice_answer,
    run_candidate_match,
    score_assessment_attempt,
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
        tenant_id = getattr(self.request, 'tenant_id', None)
        jd = self.request.FILES.get('jd_file')
        if jd:
            try:
                validate_upload_filename(jd.name)
            except DjangoValidationError as exc:
                raise ValidationError({'jd_file': str(exc)}) from exc
        serializer.save(tenant_id=tenant_id)

    def perform_update(self, serializer):
        jd = self.request.FILES.get('jd_file')
        if jd:
            try:
                validate_upload_filename(jd.name)
            except DjangoValidationError as exc:
                raise ValidationError({'jd_file': str(exc)}) from exc
        serializer.save()


class CandidateViewSet(BaseTenantViewSet):
    queryset = Candidate.objects.select_related('job', 'proposed_reporting_manager').all()
    serializer_class = CandidateSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_context(self):
        from core.tenant_utils import resolve_request_tenant_id

        ctx = super().get_serializer_context()
        ctx['tenant_id'] = resolve_request_tenant_id(self.request)
        return ctx

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, 'tenant_id', None)
        resume = self.request.FILES.get('resume_file')
        if resume:
            try:
                validate_upload_filename(resume.name)
            except DjangoValidationError as exc:
                raise ValidationError({'resume_file': str(exc)}) from exc
        instance = serializer.save(tenant_id=tenant_id)
        if resume:
            try:
                instance.parsed_resume_text = extract_text_from_file(resume)
                instance.save(update_fields=['parsed_resume_text'])
            except DjangoValidationError as exc:
                raise ValidationError({'resume_file': str(exc)}) from exc

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
        candidate = self.get_object()
        threshold = candidate.job.match_threshold or 70
        if candidate.ai_match_score < threshold:
            return Response(
                {'error': f'Match score {candidate.ai_match_score}% is below threshold {threshold}%.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        expiry_minutes = int(request.data.get('expiry_minutes', 120))
        session = create_ai_session(candidate, expiry_minutes=expiry_minutes)
        send_email = request.data.get('send_email', candidate.job.auto_send_invite)
        if send_email:
            send_interview_invite_email.delay(str(session.id))
        return Response({
            'status': 'success',
            'session_id': str(session.id),
            'magic_link': get_magic_link(session),
            'expires_at': session.expires_at,
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
    queryset = AiInterviewSession.objects.select_related('candidate', 'job').all()
    serializer_class = AiInterviewSessionSerializer

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='verify/(?P<token>[^/.]+)')
    def verify(self, request, token=None):
        try:
            session = AiInterviewSession.objects.select_related('candidate', 'job').get(magic_token=token)
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
        qs = session.questions.filter(answered_at__isnull=True).order_by('order').first()
        if not qs:
            return Response({'done': True})
        tts_payload = {'text': qs.question_text, 'voice': 'astra'}
        try:
            audio = ai_get_bytes('/api/v1/ai/tts', {'text': qs.question_text})
            import base64
            audio_b64 = base64.b64encode(audio).decode('ascii')
        except Exception:
            audio_b64 = None
        return Response({
            'done': False,
            'question': AiInterviewQuestionPublicSerializer(qs).data,
            'index': qs.order,
            'total': session.questions.count(),
            'tts_audio_base64': audio_b64,
            'tts_mime': 'audio/wav',
        })

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], parser_classes=[MultiPartParser])
    def answers(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        question_id = request.data.get('question_id')
        audio = request.FILES.get('audio')
        if not question_id or not audio:
            return Response({'error': 'question_id and audio required.'}, status=status.HTTP_400_BAD_REQUEST)
        question = AiInterviewQuestion.objects.get(pk=question_id, session=session)
        try:
            result = process_voice_answer(session, question, audio)
            session.current_question_index = question.order
            session.save(update_fields=['current_question_index'])
            return Response(result)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], url_path='complete-voice')
    def complete_voice(self, request, pk=None):
        session = AiInterviewSession.objects.get(pk=pk)
        result = complete_voice_interview(session)
        assessment_link = None
        if session.status == 'voice_passed' and session.job.assessment_enabled:
            assessment_link = f"/assessment/{session.magic_token}"
        return Response({**result, 'assessment_link': assessment_link})


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
        if not session.job.assessment_enabled:
            return Response({'error': 'Assessment disabled for this job.'}, status=status.HTTP_400_BAD_REQUEST)
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
        report = self.get_object()
        data = AiInterviewReportSerializer(report).data
        session = report.session
        data['questions'] = AiInterviewQuestionSerializer(session.questions.all(), many=True).data
        attempt = getattr(session, 'assessment_attempt', None)
        if attempt:
            data['proctor_snapshots'] = [
                {'id': str(s.id), 'captured_at': s.captured_at, 'image_path': s.image_path}
                for s in attempt.snapshots.all()[:50]
            ]
        return Response(data)
