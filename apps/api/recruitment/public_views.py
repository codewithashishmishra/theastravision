"""Public job board API (API key auth, no JWT)."""

from __future__ import annotations

from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from recruitment.document_parser import validate_upload_filename
from recruitment.job_board_auth import JobBoardApiKeyAuthentication
from recruitment.job_board_utils import job_description_html
from recruitment.models import Candidate, JobRequisition
from recruitment.tasks import run_candidate_match_task


def _published_jobs(tenant_id):
    return JobRequisition.objects.filter(
        tenant_id=tenant_id,
        is_published=True,
        status='Open',
    ).select_related('department').order_by('-published_at', '-created_at')


def _job_list_item(job):
    dept = job.department.name if job.department else None
    return {
        'id': str(job.id),
        'slug': job.slug,
        'title': job.title,
        'location': job.location,
        'department': dept,
        'employment_type': job.employment_type,
        'work_mode': job.work_mode,
        'published_at': job.published_at.isoformat() if job.published_at else None,
        'apply_deadline': str(job.apply_deadline) if job.apply_deadline else None,
        'external_apply_url': job.external_apply_url or None,
    }


def _settings_by_slug(slug: str):
    from core.addons import tenant_has_addon
    from core.models import TenantAddon
    from recruitment.models import TenantCareerPortalSettings

    try:
        settings = TenantCareerPortalSettings.objects.select_related('tenant').get(slug=slug)
    except TenantCareerPortalSettings.DoesNotExist:
        return None
    if not tenant_has_addon(settings.tenant_id, TenantAddon.ADDON_JOB_PORTAL):
        return None
    return settings


class HostedJobBoardViewSet(viewsets.ViewSet):
    """Job board by tenant slug (hosted careers page, no API key)."""

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def config(self, request, slug=None):
        settings = _settings_by_slug(slug)
        if not settings:
            return Response({'detail': 'Career portal not found.'}, status=status.HTTP_404_NOT_FOUND)
        tenant = settings.tenant
        return Response({
            'tenant_name': tenant.name,
            'slug': settings.slug,
            'logo_url': settings.logo_url,
            'primary_color': settings.primary_color,
            'company_blurb': settings.company_blurb,
        })

    def list_jobs(self, request, slug=None):
        settings = _settings_by_slug(slug)
        if not settings:
            return Response({'detail': 'Career portal not found.'}, status=status.HTTP_404_NOT_FOUND)
        jobs = _published_jobs(settings.tenant_id)
        location = request.query_params.get('location')
        department = request.query_params.get('department')
        employment_type = request.query_params.get('employment_type')
        if location:
            jobs = jobs.filter(location__icontains=location)
        if department:
            jobs = jobs.filter(department__name__icontains=department)
        if employment_type:
            jobs = jobs.filter(employment_type=employment_type)
        return Response({'results': [_job_list_item(j) for j in jobs]})

    def job_detail(self, request, slug=None, job_slug=None):
        settings = _settings_by_slug(slug)
        if not settings:
            return Response({'detail': 'Career portal not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            job = _published_jobs(settings.tenant_id).get(slug=job_slug)
        except JobRequisition.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            **_job_list_item(job),
            'description_html': job_description_html(job),
            'description_text': job.description,
            'headcount': job.headcount,
            'use_external_apply': bool(job.external_apply_url),
        })

    def apply(self, request, slug=None, job_slug=None):
        settings = _settings_by_slug(slug)
        if not settings:
            return Response({'detail': 'Career portal not found.'}, status=status.HTTP_404_NOT_FOUND)
        request.job_board_settings = settings
        request.job_board_tenant = settings.tenant
        request.tenant_id = settings.tenant_id
        view = PublicJobBoardViewSet()
        view.request = request
        view.format_kwarg = None
        return view.apply(request, slug=job_slug)


class PublicJobBoardViewSet(viewsets.ViewSet):
    authentication_classes = [JobBoardApiKeyAuthentication]
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def config(self, request):
        settings = request.job_board_settings
        tenant = request.job_board_tenant
        return Response({
            'tenant_name': tenant.name,
            'slug': settings.slug,
            'logo_url': settings.logo_url,
            'primary_color': settings.primary_color,
            'company_blurb': settings.company_blurb,
        })

    def list_jobs(self, request):
        jobs = _published_jobs(request.job_board_tenant.id)
        location = request.query_params.get('location')
        department = request.query_params.get('department')
        employment_type = request.query_params.get('employment_type')
        if location:
            jobs = jobs.filter(location__icontains=location)
        if department:
            jobs = jobs.filter(department__name__icontains=department)
        if employment_type:
            jobs = jobs.filter(employment_type=employment_type)
        return Response({'results': [_job_list_item(j) for j in jobs]})

    def job_detail(self, request, slug=None):
        try:
            job = _published_jobs(request.job_board_tenant.id).get(slug=slug)
        except JobRequisition.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
        dept = job.department.name if job.department else None
        return Response({
            **_job_list_item(job),
            'description_html': job_description_html(job),
            'description_text': job.description,
            'headcount': job.headcount,
            'use_external_apply': bool(job.external_apply_url),
        })

    def apply(self, request, slug=None):
        settings = request.job_board_settings
        origin = request.headers.get('Origin', '')
        if origin and settings.allowed_embed_origins:
            allowed = set(settings.allowed_embed_origins)
            from django.conf import settings as django_settings
            careers_url = getattr(django_settings, 'CAREERS_APP_URL', '')
            if careers_url:
                allowed.add(careers_url.rstrip('/'))
            if origin.rstrip('/') not in allowed and '*' not in allowed:
                return Response(
                    {'detail': 'Origin not allowed for applications.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            job = _published_jobs(request.job_board_tenant.id).get(slug=slug)
        except JobRequisition.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)

        if job.external_apply_url:
            return Response({'redirect_url': job.external_apply_url})

        honeypot = request.data.get('website', '')
        if honeypot:
            return Response({'status': 'ok', 'candidate_id': None})

        email = (request.data.get('email') or '').strip().lower()
        first_name = (request.data.get('first_name') or '').strip()
        last_name = (request.data.get('last_name') or '').strip()
        phone = (request.data.get('phone') or '').strip() or None
        if not email or not first_name:
            raise ValidationError({'detail': 'first_name and email are required.'})

        rate_key = f'job_apply:{job.id}:{email}'
        if cache.get(rate_key):
            return Response(
                {'detail': 'Please wait before submitting another application.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        since = timezone.now() - timedelta(hours=24)
        if Candidate.objects.filter(
            job=job, email__iexact=email, applied_on__gte=since
        ).exists():
            return Response(
                {'detail': 'You have already applied for this role recently.'},
                status=status.HTTP_409_CONFLICT,
            )

        resume = request.FILES.get('resume_file') or request.FILES.get('resume')
        if resume:
            try:
                validate_upload_filename(resume.name)
            except Exception as exc:
                raise ValidationError({'resume_file': str(exc)}) from exc

        candidate = Candidate.objects.create(
            tenant_id=job.tenant_id,
            job=job,
            first_name=first_name,
            last_name=last_name or '',
            email=email,
            phone=phone,
            stage='Sourced',
        )
        if resume:
            candidate.resume_file = resume
            candidate.save(update_fields=['resume_file'])
            from recruitment.services import extract_text_from_file
            try:
                candidate.parsed_resume_text = extract_text_from_file(resume)
                candidate.save(update_fields=['parsed_resume_text'])
            except Exception:
                pass

        cache.set(rate_key, True, timeout=300)
        run_candidate_match_task.delay(str(candidate.id))

        return Response(
            {
                'status': 'submitted',
                'candidate_id': str(candidate.id),
                'message': 'Application received. Our team will review your profile.',
            },
            status=status.HTTP_201_CREATED,
        )
