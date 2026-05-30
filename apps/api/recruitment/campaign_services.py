"""Create campaigns, import candidates, generate copy."""

from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone

from core.models import Tenant
from employees.models import Employee
from recruitment.campaign_ai import generate_outreach_copy
from recruitment.campaign_import import parse_candidate_file
from recruitment.document_parser import parse_uploaded_file
from recruitment.job_board_utils import unique_job_slug
from recruitment.models import Candidate, JobRequisition, RecruitmentCampaign


def _tenant_company_name(tenant_id) -> str:
    tenant = Tenant.objects.filter(pk=tenant_id).first()
    return tenant.name if tenant else 'Our company'


@transaction.atomic
def create_campaign_from_request(
    *,
    tenant_id,
    user,
    title: str,
    jd_file,
    default_reporting_manager_id,
    candidate_file,
) -> RecruitmentCampaign:
    manager = Employee.objects.get(pk=default_reporting_manager_id, tenant_id=tenant_id)
    jd_text = ''
    if jd_file:
        jd_text = parse_uploaded_file(jd_file)

    slug = unique_job_slug(tenant_id, title)
    job = JobRequisition.objects.create(
        tenant_id=tenant_id,
        title=title.strip(),
        location='Remote',
        description=jd_text or title.strip(),
        status='Open',
        match_threshold=70,
        slug=slug,
    )
    if jd_file:
        job.jd_file = jd_file
        job.save(update_fields=['jd_file', 'updated_at'])

    company = _tenant_company_name(tenant_id)
    copy = generate_outreach_copy(title, jd_text, company)
    campaign = RecruitmentCampaign.objects.create(
        tenant_id=tenant_id,
        title=title.strip(),
        job=job,
        default_reporting_manager=manager,
        created_by=user,
        outreach_subject=copy['subject'],
        outreach_body_html=copy['body_html'],
        outreach_body_text=copy.get('body_text', ''),
    )
    rows, _ = _collect_import_rows(candidate_file)
    _import_candidates(campaign, rows)
    return campaign


def _collect_import_rows(candidate_file) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    rows: list[dict] = []
    if candidate_file:
        file_rows, file_errors = parse_candidate_file(candidate_file)
        rows.extend(file_rows)
        errors.extend(file_errors)
    seen: set[str] = set()
    unique_rows: list[dict] = []
    for row in rows:
        if row['email'] in seen:
            continue
        seen.add(row['email'])
        unique_rows.append(row)
    return unique_rows, errors


def import_candidates_to_campaign(
    campaign: RecruitmentCampaign,
    *,
    candidate_file,
) -> tuple[int, list[str]]:
    rows, errors = _collect_import_rows(candidate_file)
    created = _import_candidates(campaign, rows)
    return created, errors


def _import_candidates(campaign: RecruitmentCampaign, rows: list[dict]) -> int:
    created = 0
    for row in rows:
        _, was_created = Candidate.objects.get_or_create(
            tenant_id=campaign.tenant_id,
            job=campaign.job,
            email=row['email'],
            defaults={
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'campaign': campaign,
                'proposed_reporting_manager': campaign.default_reporting_manager,
                'portal_token': uuid.uuid4(),
                'outreach_status': Candidate.OUTREACH_PENDING,
            },
        )
        if was_created:
            created += 1
    return created


def regenerate_campaign_copy(campaign: RecruitmentCampaign) -> RecruitmentCampaign:
    company = _tenant_company_name(campaign.tenant_id)
    jd_text = campaign.job.description or ''
    copy = generate_outreach_copy(campaign.title, jd_text, company)
    campaign.outreach_subject = copy['subject']
    campaign.outreach_body_html = copy['body_html']
    campaign.outreach_body_text = copy.get('body_text', '')
    campaign.save(
        update_fields=[
            'outreach_subject',
            'outreach_body_html',
            'outreach_body_text',
            'updated_at',
        ]
    )
    return campaign


def campaign_stats(campaign: RecruitmentCampaign) -> dict:
    qs = Candidate.objects.filter(campaign=campaign)
    threshold = campaign.job.match_threshold or 70
    return {
        'total_candidates': qs.count(),
        'pending': qs.filter(outreach_status=Candidate.OUTREACH_PENDING).count(),
        'sent': qs.filter(outreach_status=Candidate.OUTREACH_SENT).count(),
        'matched': qs.filter(outreach_status=Candidate.OUTREACH_MATCHED).count(),
        'above_threshold': qs.filter(ai_match_score__gte=threshold).count(),
    }
