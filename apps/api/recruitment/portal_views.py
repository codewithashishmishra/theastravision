"""Public candidate portal (magic link, no JWT)."""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from recruitment.document_parser import validate_upload_filename
from recruitment.models import Candidate
from recruitment.services import extract_text_from_file, get_magic_link, run_candidate_match


TERMINAL_SESSION_STATUSES = {'completed', 'failed', 'expired'}


def _mask_email(email: str) -> str:
    if '@' not in email:
        return '***'
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return f'{local[0]}***@{domain}'
    return f'{local[0]}***{local[-1]}@{domain}'


def _portal_invalid_reason(candidate: Candidate) -> str | None:
    if candidate.outreach_status == Candidate.OUTREACH_COMPLETED:
        return 'This link has already been used for a completed process.'
    active = candidate.ai_sessions.exclude(status__in=TERMINAL_SESSION_STATUSES).order_by('-created_at').first()
    if active and active.status in ('completed', 'failed', 'expired'):
        return 'Your interview process is complete.'
    return None


class CampaignPortalVerifyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token=None):
        try:
            candidate = Candidate.objects.select_related('job', 'campaign').get(portal_token=token)
        except Candidate.DoesNotExist:
            return Response({'error': 'Invalid or expired link.'}, status=status.HTTP_404_NOT_FOUND)

        invalid = _portal_invalid_reason(candidate)
        if invalid:
            return Response({'error': invalid}, status=status.HTTP_403_FORBIDDEN)

        session = candidate.ai_sessions.exclude(status__in=TERMINAL_SESSION_STATUSES).order_by('-created_at').first()
        interview_link = get_magic_link(session) if session else None

        return Response({
            'job_title': candidate.job.title,
            'email_masked': _mask_email(candidate.email),
            'first_name': candidate.first_name,
            'resume_uploaded': bool(candidate.resume_file or candidate.parsed_resume_text),
            'ai_match_score': candidate.ai_match_score,
            'match_threshold': candidate.job.match_threshold or 70,
            'outreach_status': candidate.outreach_status,
            'interview_link': interview_link,
        })


class CampaignPortalResumeView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, token=None):
        try:
            candidate = Candidate.objects.select_related('job').get(portal_token=token)
        except Candidate.DoesNotExist:
            return Response({'error': 'Invalid link.'}, status=status.HTTP_404_NOT_FOUND)

        invalid = _portal_invalid_reason(candidate)
        if invalid:
            return Response({'error': invalid}, status=status.HTTP_403_FORBIDDEN)

        resume = request.FILES.get('resume') or request.FILES.get('resume_file')
        if not resume:
            return Response({'detail': 'Resume file is required (field: resume).'}, status=400)
        try:
            validate_upload_filename(resume.name)
        except DjangoValidationError as exc:
            raise ValidationError({'resume': str(exc)}) from exc

        from recruitment.models import JobRequisition
        from recruitment.tasks import parse_resume_and_match_task

        candidate.resume_file = resume
        candidate.outreach_status = Candidate.OUTREACH_RESUME_UPLOADED
        candidate.resume_parse_status = JobRequisition.PARSE_PROCESSING
        candidate.save(
            update_fields=['resume_file', 'outreach_status', 'resume_parse_status', 'updated_at']
        )
        parse_resume_and_match_task.delay(str(candidate.id))
        threshold = candidate.job.match_threshold or 70
        return Response(
            {
                'status': 'processing',
                'candidate_id': str(candidate.id),
                'resume_parse_status': candidate.resume_parse_status,
                'threshold': threshold,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class CampaignPortalParseStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token=None):
        try:
            candidate = Candidate.objects.select_related('job').get(portal_token=token)
        except Candidate.DoesNotExist:
            return Response({'error': 'Invalid link.'}, status=status.HTTP_404_NOT_FOUND)

        threshold = candidate.job.match_threshold or 70
        return Response({
            'resume_parse_status': candidate.resume_parse_status,
            'resume_parse_error': candidate.resume_parse_error,
            'ai_match_score': candidate.ai_match_score,
            'match_passed': candidate.ai_match_score >= threshold,
            'threshold': threshold,
            'match_breakdown': candidate.match_breakdown,
        })
