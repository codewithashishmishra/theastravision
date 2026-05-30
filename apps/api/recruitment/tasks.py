import time

from celery import shared_task
from django.utils import timezone


@shared_task
def send_campaign_outreach_batch(campaign_id: str, candidate_ids: list[str]):
    from recruitment.campaign_email import send_campaign_outreach
    from recruitment.models import Candidate, RecruitmentCampaign

    try:
        campaign = RecruitmentCampaign.objects.get(pk=campaign_id)
    except RecruitmentCampaign.DoesNotExist:
        return

    if campaign.status == RecruitmentCampaign.STATUS_PAUSED:
        return

    rate = max(1, campaign.send_rate_per_minute or 10)
    delay = 60.0 / rate

    try:
        from cold_campaign.email_service import build_smtp_connection

        conn = build_smtp_connection()
    except ValueError:
        campaign.status = RecruitmentCampaign.STATUS_PAUSED
        campaign.save(update_fields=['status', 'updated_at'])
        return

    try:
        for cid in candidate_ids:
            campaign.refresh_from_db(fields=['status'])
            if campaign.status == RecruitmentCampaign.STATUS_PAUSED:
                break
            try:
                candidate = Candidate.objects.get(
                    pk=cid,
                    campaign=campaign,
                    outreach_status=Candidate.OUTREACH_PENDING,
                )
            except Candidate.DoesNotExist:
                continue
            try:
                send_campaign_outreach(campaign, candidate, connection=conn)
                candidate.outreach_status = Candidate.OUTREACH_SENT
                candidate.outreach_sent_at = timezone.now()
                candidate.save(update_fields=['outreach_status', 'outreach_sent_at', 'updated_at'])
            except Exception:
                pass
            time.sleep(delay)
    finally:
        conn.close()

    _finalize_recruitment_campaign(campaign_id)


def _finalize_recruitment_campaign(campaign_id: str):
    from recruitment.models import RecruitmentCampaign

    campaign = RecruitmentCampaign.objects.get(pk=campaign_id)
    if campaign.status == RecruitmentCampaign.STATUS_PAUSED:
        return
    pending = campaign.candidates.filter(outreach_status='pending').exists()
    if pending:
        return
    campaign.status = RecruitmentCampaign.STATUS_SENT
    campaign.save(update_fields=['status', 'updated_at'])


@shared_task
def dispatch_campaign_outreach(campaign_id: str):
    from recruitment.models import RecruitmentCampaign

    campaign = RecruitmentCampaign.objects.get(pk=campaign_id)
    pending_ids = [
        str(x)
        for x in campaign.candidates.filter(outreach_status='pending').values_list('id', flat=True)
    ]
    if not pending_ids:
        campaign.status = RecruitmentCampaign.STATUS_SENT
        campaign.save(update_fields=['status', 'updated_at'])
        return
    send_campaign_outreach_batch.delay(campaign_id, pending_ids)


@shared_task
def send_interview_invite_email(session_id: str):
    from recruitment.models import AiInterviewSession
    from recruitment.email_service import send_interview_invite

    session = AiInterviewSession.objects.select_related(
        'candidate', 'candidate__tenant', 'job', 'job__tenant'
    ).get(pk=session_id)
    send_interview_invite(session)
    session.invite_sent_at = timezone.now()
    session.save(update_fields=['invite_sent_at'])


def schedule_interview_invite_email(session_id: str, scheduled_at=None):
    """Send immediately or at scheduled_at (aware datetime)."""
    if scheduled_at and scheduled_at > timezone.now():
        send_interview_invite_email.apply_async(args=[session_id], eta=scheduled_at)
    else:
        send_interview_invite_email.delay(session_id)


@shared_task
def generate_and_email_report(session_id: str):
    from recruitment.services import finalize_interview_report

    finalize_interview_report(session_id)


@shared_task
def async_background_report_generation(session_id: str):
    from recruitment.services import async_background_report_generation as generate_report

    return generate_report(session_id)


@shared_task
def parse_job_jd_task(job_id: str):
    from recruitment.models import JobRequisition
    from recruitment.services import extract_text_from_file, pre_generate_campaign_questions

    job = JobRequisition.objects.get(pk=job_id)
    job.jd_parse_status = JobRequisition.PARSE_PROCESSING
    job.save(update_fields=['jd_parse_status', 'updated_at'])
    try:
        if not job.jd_file:
            job.jd_parse_status = JobRequisition.PARSE_READY
            job.save(update_fields=['jd_parse_status', 'updated_at'])
            return
        job.jd_file.open('rb')
        text = extract_text_from_file(job.jd_file)
        job.description = text or job.description
        job.jd_parse_status = JobRequisition.PARSE_READY
        job.jd_parse_error = ''
        job.save(update_fields=['description', 'jd_parse_status', 'jd_parse_error', 'updated_at'])
        if hasattr(job, 'recruitment_campaign'):
            pre_generate_campaign_questions(str(job.recruitment_campaign.id))
    except Exception as exc:
        job.jd_parse_status = JobRequisition.PARSE_FAILED
        job.jd_parse_error = str(exc)[:500]
        job.save(update_fields=['jd_parse_status', 'jd_parse_error', 'updated_at'])


@shared_task
def parse_resume_and_match_task(candidate_id: str):
    from recruitment.models import Candidate
    from recruitment.services import (
        extract_text_from_file,
        pre_generate_candidate_questions,
        run_candidate_match,
    )

    from recruitment.models import JobRequisition

    candidate = Candidate.objects.select_related('job').get(pk=candidate_id)
    candidate.resume_parse_status = JobRequisition.PARSE_PROCESSING
    candidate.save(update_fields=['resume_parse_status', 'updated_at'])
    try:
        if candidate.resume_file and not candidate.parsed_resume_text:
            candidate.resume_file.open('rb')
            candidate.parsed_resume_text = extract_text_from_file(candidate.resume_file)
            candidate.save(update_fields=['parsed_resume_text', 'updated_at'])
        run_candidate_match(candidate)
        if candidate.ai_match_score >= 70:
            pre_generate_candidate_questions(candidate)
        candidate.resume_parse_status = JobRequisition.PARSE_READY
        candidate.resume_parse_error = ''
        candidate.save(update_fields=['resume_parse_status', 'resume_parse_error', 'updated_at'])
    except Exception as exc:
        candidate.resume_parse_status = JobRequisition.PARSE_FAILED
        candidate.resume_parse_error = str(exc)[:500]
        candidate.save(update_fields=['resume_parse_status', 'resume_parse_error', 'updated_at'])


@shared_task
def run_candidate_match_task(candidate_id: str):
    from recruitment.models import Candidate
    from recruitment.services import run_candidate_match

    candidate = Candidate.objects.select_related('job').get(pk=candidate_id)
    run_candidate_match(candidate)


@shared_task
def cleanup_expired_sessions():
    from recruitment.models import AiInterviewSession

    # Only expire sessions that have an explicit expires_at in the past.
    AiInterviewSession.objects.filter(
        expires_at__isnull=False,
        expires_at__lt=timezone.now(),
        status__in=['pending', 'active'],
    ).update(status='expired')


@shared_task
def purge_expired_interview_media():
    """Delete interview chunks/blobs and legacy files past tenant retention."""
    from datetime import timedelta

    from django.db.models import Q

    from recruitment.interview_storage import InterviewStorageService
    from recruitment.models import (
        AiInterviewMediaBlob,
        AiInterviewMediaChunk,
        AiInterviewSession,
        TenantRecruitmentSettings,
    )

    now = timezone.now()
    for policy in TenantRecruitmentSettings.objects.all():
        days = policy.interview_recording_retention_days or 15
        cutoff = now - timedelta(days=days)
        sessions = AiInterviewSession.objects.filter(
            tenant_id=policy.tenant_id,
            status__in=['completed', 'failed', 'expired'],
        ).filter(
            Q(recording_ended_at__lt=cutoff)
            | Q(recording_ended_at__isnull=True, updated_at__lt=cutoff)
        )
        for session in sessions[:200]:
            AiInterviewMediaChunk.objects.filter(session=session).delete()
            AiInterviewMediaBlob.objects.filter(session=session).delete()
            if session.session_recording_path and not session.session_recording_path.startswith('blob:'):
                InterviewStorageService.delete_path(session.session_recording_path)
            if session.camera_recording_path and not session.camera_recording_path.startswith('blob:'):
                InterviewStorageService.delete_path(session.camera_recording_path)
            for q in session.questions.all():
                if q.audio_path and not q.audio_path.startswith('blob:'):
                    InterviewStorageService.delete_path(q.audio_path)
                q.audio_path = ''
                q.save(update_fields=['audio_path', 'updated_at'])
            session.session_recording_path = ''
            session.camera_recording_path = ''
            session.save(update_fields=['session_recording_path', 'camera_recording_path', 'updated_at'])
