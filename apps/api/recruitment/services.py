"""Business logic for AI interviews."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.utils import timezone

from recruitment.ai_client import (
    ai_post,
    pre_generate_campaign_questions as ai_pre_generate_campaign_questions,
    pre_generate_candidate_questions as ai_pre_generate_candidate_questions,
    semantic_evaluate_answer,
)
from recruitment.conversation import ConversationManager
from recruitment.answer_scoring import score_answer
from recruitment.document_parser import parse_uploaded_file
from recruitment.email_service import get_frontend_base_url, send_report_to_hr
from recruitment.interview_storage import InterviewStorageService
from recruitment.live_events import emit_session_ended, emit_transcript_segment
from recruitment.matching import compute_match
from recruitment.models import (
    AiInterviewQuestion,
    AiInterviewReport,
    AiInterviewSession,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentTemplate,
    Candidate,
    CandidatePrebakedQuestion,
    CandidateLiveResponse,
    RecruitmentCampaignAttachment,
    RecruitmentCampaignQuestion,
)
from recruitment.report_builder import build_report
from recruitment.translation import to_english


def extract_text_from_file(uploaded_file) -> str:
    return parse_uploaded_file(uploaded_file)


def run_candidate_match(candidate: Candidate) -> dict:
    job = candidate.job
    resume_text = candidate.parsed_resume_text
    if not resume_text and candidate.resume_file:
        candidate.resume_file.open('rb')
        resume_text = extract_text_from_file(candidate.resume_file)
        candidate.parsed_resume_text = resume_text
    jd_text = job.description
    if job.jd_file:
        job.jd_file.open('rb')
        jd_text = extract_text_from_file(job.jd_file) or jd_text
    result = compute_match(job.title, jd_text, resume_text)
    candidate.ai_match_score = int(result.get('score', 0))
    candidate.match_breakdown = {
        'strengths': result.get('strengths', []),
        'weaknesses': result.get('weaknesses', []),
        'recommendation': result.get('recommendation', ''),
        'skills_met': result.get('skills_met', []),
        'skills_missed': result.get('skills_missed', []),
    }
    update_fields = ['ai_match_score', 'match_breakdown', 'parsed_resume_text']
    threshold = job.match_threshold or 70
    if candidate.campaign_id and candidate.ai_match_score >= threshold:
        if candidate.outreach_status in (
            Candidate.OUTREACH_SENT,
            Candidate.OUTREACH_OPENED,
            Candidate.OUTREACH_RESUME_UPLOADED,
            Candidate.OUTREACH_MATCHED,
        ):
            candidate.outreach_status = Candidate.OUTREACH_MATCHED
            update_fields.append('outreach_status')
    candidate.save(update_fields=update_fields)
    return result


def _normalize_tier(value: str) -> str:
    val = (value or '').strip().lower().replace(' ', '_')
    if val in {
        CandidatePrebakedQuestion.TIER_LOW,
        CandidatePrebakedQuestion.TIER_MEDIUM,
        CandidatePrebakedQuestion.TIER_HARD,
        CandidatePrebakedQuestion.TIER_EXTREME_HARD,
    }:
        return val
    return CandidatePrebakedQuestion.TIER_MEDIUM


def pre_generate_campaign_questions(campaign_id: str) -> int:
    from recruitment.models import RecruitmentCampaign

    campaign = RecruitmentCampaign.objects.select_related('job').get(pk=campaign_id)
    job = campaign.job
    jd_text = job.description or ''
    if job.jd_file:
        job.jd_file.open('rb')
        jd_text = extract_text_from_file(job.jd_file) or jd_text
    if not jd_text.strip():
        return 0
    RecruitmentCampaignAttachment.objects.update_or_create(
        tenant_id=campaign.tenant_id,
        campaign=campaign,
        kind=RecruitmentCampaignAttachment.KIND_JD_EXTRACT,
        defaults={
            'file_path': str(getattr(job.jd_file, 'name', '') or ''),
            'extracted_text': jd_text,
        },
    )
    questions = ai_pre_generate_campaign_questions(str(campaign.id), job.title, jd_text)
    if not questions:
        return 0
    RecruitmentCampaignQuestion.objects.filter(
        campaign=campaign,
        source=RecruitmentCampaignQuestion.SOURCE_JD_BASELINE,
    ).delete()
    for idx, row in enumerate(questions[:5], start=1):
        RecruitmentCampaignQuestion.objects.create(
            tenant_id=campaign.tenant_id,
            campaign=campaign,
            order=idx,
            source=RecruitmentCampaignQuestion.SOURCE_JD_BASELINE,
            difficulty_tier=_normalize_tier(row.get('difficulty_tier') or 'medium'),
            question_text=(row.get('question') or '').strip(),
            ideal_answer=(row.get('ideal_answer') or '').strip(),
        )
    return min(len(questions), 5)


def pre_generate_candidate_questions(candidate: Candidate) -> int:
    if candidate.ai_match_score < 70:
        return 0
    job = candidate.job
    jd_text = job.description or ''
    if job.jd_file:
        job.jd_file.open('rb')
        jd_text = extract_text_from_file(job.jd_file) or jd_text
    resume_text = candidate.parsed_resume_text or ''
    experience_summary = f"match_score={candidate.ai_match_score}; stage={candidate.stage}"
    questions = ai_pre_generate_candidate_questions(
        str(candidate.id),
        str(candidate.campaign_id) if candidate.campaign_id else None,
        job.title,
        jd_text,
        resume_text,
        experience_summary,
    )
    if not questions:
        return 0
    CandidatePrebakedQuestion.objects.filter(candidate=candidate, session__isnull=True).delete()
    for idx, row in enumerate(questions[:5], start=1):
        CandidatePrebakedQuestion.objects.create(
            tenant_id=candidate.tenant_id,
            candidate=candidate,
            campaign=candidate.campaign,
            order=idx,
            difficulty_tier=_normalize_tier(row.get('difficulty_tier') or 'medium'),
            question_text=(row.get('question') or '').strip(),
            ideal_benchmarked_response=(row.get('ideal_answer') or '').strip(),
        )
    return min(len(questions), 5)


def create_ai_session(
    candidate: Candidate,
    expiry_minutes: int | None = 120,
    *,
    include_assessment: bool = False,
) -> AiInterviewSession:
    """Create session with optional link expiry (minutes from now)."""
    expires_at = None
    if expiry_minutes:
        expires_at = timezone.now() + timedelta(minutes=int(expiry_minutes))
    session = AiInterviewSession.objects.create(
        tenant_id=candidate.tenant_id,
        candidate=candidate,
        job=candidate.job,
        status='pending',
        magic_token=uuid.uuid4(),
        expires_at=expires_at,
        include_assessment=bool(include_assessment),
    )
    if candidate.campaign_id:
        candidate.outreach_status = 'completed'
        candidate.save(update_fields=['outreach_status', 'updated_at'])
    # Attach candidate-level pre-generated questions to this new session.
    CandidatePrebakedQuestion.objects.filter(
        candidate=candidate, session__isnull=True
    ).update(session=session, updated_at=timezone.now())
    return session


def get_magic_link(session: AiInterviewSession) -> str:
    return f"{get_frontend_base_url()}/interview/join/{session.magic_token}"


def ensure_questions(session: AiInterviewSession) -> None:
    if session.questions.exists():
        return
    candidate = session.candidate
    job = session.job
    count = job.interview_question_count or 5
    prebaked = list(session.prebaked_questions.all().order_by('order'))
    if prebaked:
        for idx, q in enumerate(prebaked, start=1):
            AiInterviewQuestion.objects.create(
                tenant_id=session.tenant_id,
                session=session,
                order=idx,
                question_text=q.question_text,
                ideal_answer=q.ideal_benchmarked_response,
                rubric=f"tier:{q.difficulty_tier}",
            )
        return
    result = ai_post('/api/v1/ai/generate-questions', {
        'job_title': job.title,
        'job_description': candidate.job.description,
        'resume_text': candidate.parsed_resume_text or f"{candidate.first_name} {candidate.last_name}",
        'count': count,
    })
    for idx, q in enumerate(result.get('questions', [])[:count], start=1):
        AiInterviewQuestion.objects.create(
            tenant_id=session.tenant_id,
            session=session,
            order=idx,
            question_text=q.get('question', ''),
            ideal_answer=q.get('ideal_answer', ''),
            rubric=q.get('rubric', ''),
        )


SKIP_LIMIT = 3


def count_skipped_questions(session: AiInterviewSession) -> int:
    return session.questions.filter(skipped=True).count()


def end_interview_skip_limit(session: AiInterviewSession) -> None:
    flags = dict(session.proctor_flags or {})
    flags['skip_limit_exceeded'] = True
    session.proctor_flags = flags
    session.status = 'failed'
    session.save(update_fields=['proctor_flags', 'status', 'updated_at'])
    emit_session_ended(session.id, status=session.status)


def skip_voice_question(session: AiInterviewSession, question: AiInterviewQuestion) -> dict:
    conversation = ConversationManager()
    question.skipped = True
    question.answered_at = timezone.now()
    question.candidate_transcript = ''
    question.score_percent = None
    question.save(
        update_fields=['skipped', 'answered_at', 'candidate_transcript', 'score_percent', 'updated_at']
    )
    emit_transcript_segment(
        session.id,
        speaker='Candidate',
        text='[Question skipped]',
        question_order=question.order,
        is_final=True,
    )
    session.current_question_index = question.order
    session.save(update_fields=['current_question_index', 'updated_at'])
    conversation.finalize_turn(
        session,
        question,
        '',
        status=CandidateLiveResponse.STATUS_SKIPPED,
        silence_seconds=5,
    )
    skip_count = count_skipped_questions(session)
    if skip_count >= SKIP_LIMIT:
        end_interview_skip_limit(session)
        return {
            'skip_count': skip_count,
            'skip_limit': SKIP_LIMIT,
            'skip_limit_exceeded': True,
            'ended': True,
        }
    return {
        'skip_count': skip_count,
        'skip_limit': SKIP_LIMIT,
        'skip_limit_exceeded': False,
        'ended': False,
    }


def process_voice_answer(session: AiInterviewSession, question: AiInterviewQuestion, audio_file) -> dict:
    conversation = ConversationManager()
    audio_bytes = audio_file.read()
    if InterviewStorageService.use_pg_blobs():
        blob = InterviewStorageService.save_answer_audio_blob(
            session, question.order, audio_bytes, content_type='audio/webm'
        )
        question.audio_path = f'blob:{blob.id}'
    else:
        rel = f"interviews/{session.tenant_id}/{session.id}/q{question.order}.webm"
        path = InterviewStorageService.save_bytes(rel, audio_bytes)
        question.audio_path = path
    try:
        transcribe = conversation.stream_candidate_stt(
            audio_bytes,
            filename=f'answer_{question.order}.webm',
        )
    except Exception:
        transcribe = ai_post(
            '/api/v1/ai/transcribe',
            files={'audio': (f'answer_{question.order}.webm', audio_bytes, 'audio/webm')},
        )
    detected_lang = transcribe.get('detected_language', 'en')
    raw_text = transcribe.get('text', '')
    transcript = to_english(raw_text, detected_lang)
    question.candidate_transcript = transcript
    eval_result = score_answer(question.ideal_answer, transcript)
    question.score_percent = float(eval_result.get('score_percent', 0))
    question.answered_at = timezone.now()
    question.save()
    emit_transcript_segment(
        session.id,
        speaker='Candidate',
        text=transcript,
        question_order=question.order,
        is_final=True,
    )
    conversation.finalize_turn(
        session,
        question,
        transcript,
        status=CandidateLiveResponse.STATUS_ANSWERED,
    )
    return {
        'transcript': transcript,
        'score_percent': question.score_percent,
        'feedback': eval_result.get('feedback'),
        'detected_language': detected_lang,
    }


def complete_voice_interview(session: AiInterviewSession) -> dict:
    scores = [q.score_percent for q in session.questions.all() if q.score_percent is not None]
    overall = sum(scores) / len(scores) if scores else 0
    session.overall_voice_score = overall
    threshold = session.job.voice_pass_threshold or 60
    passed = overall >= threshold
    if passed:
        session.status = 'voice_passed' if session.include_assessment else 'completed'
    else:
        session.status = 'failed'
    session.save(update_fields=['overall_voice_score', 'status'])
    if session.status == 'completed':
        finalize_interview_report(str(session.id))
        from recruitment.tasks import async_background_report_generation as async_report_task

        async_report_task.apply_async(args=[str(session.id)], countdown=30 * 60)
    elif session.status == 'voice_passed' and session.include_assessment:
        ensure_assessment_template(session)
    return {'passed': passed, 'overall_voice_score': overall, 'status': session.status}


def ensure_assessment_template(session: AiInterviewSession) -> AssessmentTemplate:
    job = session.job
    template, created = AssessmentTemplate.objects.get_or_create(
        tenant_id=session.tenant_id,
        job=job,
        defaults={'duration_minutes': 20, 'question_count': 10},
    )
    if created or template.questions.count() == 0:
        result = ai_post('/api/v1/ai/generate-assessment', {
            'job_title': job.title,
            'job_description': job.description,
            'resume_text': session.candidate.parsed_resume_text,
            'count': template.question_count,
        })
        template.questions.all().delete()
        for idx, q in enumerate(result.get('questions', []), start=1):
            opts = q.get('options', {})
            AssessmentQuestion.objects.create(
                tenant_id=session.tenant_id,
                template=template,
                order=idx,
                prompt=q.get('prompt', ''),
                option_a=opts.get('A', ''),
                option_b=opts.get('B', ''),
                option_c=opts.get('C', ''),
                option_d=opts.get('D', ''),
                correct_option=q.get('correct_option', 'A'),
            )
    return template


def score_assessment_attempt(attempt: AssessmentAttempt) -> float:
    template = attempt.session.job.assessment_template
    questions = list(template.questions.all())
    correct = 0
    for q in questions:
        if attempt.answers.get(str(q.id)) == q.correct_option:
            correct += 1
    score = (correct / len(questions) * 100) if questions else 0
    attempt.score = score
    attempt.submitted_at = timezone.now()
    attempt.save(update_fields=['score', 'submitted_at'])
    session = attempt.session
    session.assessment_score = score
    session.status = 'completed'
    session.save(update_fields=['assessment_score', 'status'])
    finalize_interview_report(str(session.id))
    from recruitment.tasks import async_background_report_generation as async_report_task

    async_report_task.apply_async(args=[str(session.id)], countdown=30 * 60)
    return score


def finalize_interview_report(session_id: str) -> AiInterviewReport:
    session = AiInterviewSession.objects.select_related('candidate', 'job').prefetch_related('questions').get(pk=session_id)
    candidate = session.candidate
    job = session.job
    questions_payload = [
        {
            'question': q.question_text,
            'transcript': q.candidate_transcript,
            'score_percent': q.score_percent,
        }
        for q in session.questions.all()
    ]
    report_data = build_report(
        candidate_name=f"{candidate.first_name} {candidate.last_name}",
        job_title=job.title,
        match_score=candidate.ai_match_score,
        voice_score=session.overall_voice_score,
        assessment_score=session.assessment_score,
        questions=questions_payload,
        session_status=session.status,
    )
    report, _ = AiInterviewReport.objects.update_or_create(
        tenant_id=session.tenant_id,
        session=session,
        defaults={
            'summary_html': report_data.get('summary_html', ''),
            'summary_json': report_data.get('summary_json', {}),
        },
    )
    try:
        send_report_to_hr(session, report)
        report.emailed_at = timezone.now()
        report.save(update_fields=['emailed_at'])
    except Exception:
        pass
    return report


def build_semantic_interview_report(session: AiInterviewSession) -> dict:
    turns = []
    for q in session.questions.all().order_by('order'):
        candidate_answer = q.candidate_transcript or ''
        if q.skipped:
            turns.append({
                'order': q.order,
                'question': q.question_text,
                'status': 'skipped',
                'score_out_of_10': 0,
                'feedback': 'Skipped by candidate.',
                'candidate_answer': '',
            })
            continue
        eval_json = semantic_evaluate_answer(
            question=q.question_text,
            benchmark_answer=q.ideal_answer,
            candidate_answer=candidate_answer,
        )
        turns.append({
            'order': q.order,
            'question': q.question_text,
            'candidate_answer': candidate_answer,
            'benchmark_answer': q.ideal_answer,
            'score_out_of_10': eval_json.get('score_out_of_10', 0),
            'feedback': eval_json.get('feedback', ''),
            'strengths': eval_json.get('strengths', []),
            'gaps': eval_json.get('gaps', []),
        })
    return {
        'session_id': str(session.id),
        'candidate_id': str(session.candidate_id),
        'generated_at': timezone.now().isoformat(),
        'turns': turns,
    }


def async_background_report_generation(session_id: str) -> dict:
    session = (
        AiInterviewSession.objects.select_related('candidate', 'job')
        .prefetch_related('questions')
        .get(pk=session_id)
    )
    report_payload = build_semantic_interview_report(session)
    report, _ = AiInterviewReport.objects.update_or_create(
        tenant_id=session.tenant_id,
        session=session,
        defaults={
            'summary_json': {
                **(report_payload or {}),
                'final_interview_report_filename': 'final_interview_report.json',
            },
            'summary_html': '',
        },
    )
    return {'report_id': str(report.id), 'session_id': str(session.id)}
