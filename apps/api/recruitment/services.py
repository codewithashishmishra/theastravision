"""Business logic for AI interviews."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.utils import timezone

from recruitment.ai_client import ai_post
from recruitment.answer_scoring import score_answer
from recruitment.document_parser import parse_uploaded_file
from recruitment.email_service import get_frontend_base_url, send_report_to_hr
from recruitment.interview_storage import InterviewStorageService
from recruitment.matching import compute_match
from recruitment.models import (
    AiInterviewQuestion,
    AiInterviewReport,
    AiInterviewSession,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentTemplate,
    Candidate,
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
    candidate.save(update_fields=['ai_match_score', 'match_breakdown', 'parsed_resume_text'])
    return result


def create_ai_session(candidate: Candidate, expiry_minutes: int = 120) -> AiInterviewSession:
    session = AiInterviewSession.objects.create(
        tenant_id=candidate.tenant_id,
        candidate=candidate,
        job=candidate.job,
        status='pending',
        magic_token=uuid.uuid4(),
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
    )
    return session


def get_magic_link(session: AiInterviewSession) -> str:
    return f"{get_frontend_base_url()}/interview/join/{session.magic_token}"


def ensure_questions(session: AiInterviewSession) -> None:
    if session.questions.exists():
        return
    candidate = session.candidate
    job = session.job
    count = job.interview_question_count or 5
    result = ai_post('/api/v1/ai/generate-questions', {
        'job_title': job.title,
        'job_description': candidate.job.description,
        'resume_text': candidate.parsed_resume_text or f"{candidate.first_name} {candidate.last_name}",
        'count': count,
    })
    for idx, q in enumerate(result.get('questions', []), start=1):
        AiInterviewQuestion.objects.create(
            tenant_id=session.tenant_id,
            session=session,
            order=idx,
            question_text=q.get('question', ''),
            ideal_answer=q.get('ideal_answer', ''),
            rubric=q.get('rubric', ''),
        )


def process_voice_answer(session: AiInterviewSession, question: AiInterviewQuestion, audio_file) -> dict:
    rel = f"interviews/{session.tenant_id}/{session.id}/q{question.order}.webm"
    path = InterviewStorageService.save_upload(rel, audio_file)
    question.audio_path = path
    with InterviewStorageService.open_path(path) as f:
        audio_bytes = f.read()
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
        session.status = 'voice_passed' if session.job.assessment_enabled else 'completed'
    else:
        session.status = 'failed'
    session.save(update_fields=['overall_voice_score', 'status'])
    if session.status == 'completed':
        finalize_interview_report(str(session.id))
    elif session.status == 'voice_passed':
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
