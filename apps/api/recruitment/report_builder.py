"""Deterministic HR interview reports — no LLM."""

from __future__ import annotations

from django.template.loader import render_to_string


def _recommendation(match: int, voice: float | None, assessment: float | None) -> str:
    voice = voice or 0
    assessment = assessment if assessment is not None else voice
    composite = 0.3 * match + 0.5 * voice + 0.2 * assessment
    if composite >= 75:
        return 'hire'
    if composite >= 55:
        return 'review'
    return 'reject'


def build_report(
    *,
    candidate_name: str,
    job_title: str,
    match_score: int,
    voice_score: float | None,
    assessment_score: float | None,
    questions: list[dict],
    session_status: str = 'completed',
) -> dict:
    rec = _recommendation(match_score, voice_score, assessment_score)
    rec_label = {'hire': 'Recommend hire', 'review': 'Needs HR review', 'reject': 'Do not proceed'}[rec]

    strengths = []
    if match_score >= 70:
        strengths.append(f'Resume–JD match {match_score}% meets threshold')
    if voice_score is not None and voice_score >= 60:
        strengths.append(f'Voice interview average {voice_score:.0f}%')
    if assessment_score is not None and assessment_score >= 60:
        strengths.append(f'Online assessment {assessment_score:.0f}%')

    risks = []
    if match_score < 70:
        risks.append(f'Resume match below 70% ({match_score}%)')
    if voice_score is not None and voice_score < 60:
        risks.append(f'Voice interview below pass threshold ({voice_score:.0f}%)')
    if assessment_score is not None and assessment_score < 60:
        risks.append(f'Assessment score low ({assessment_score:.0f}%)')

    summary_json = {
        'recommendation': rec,
        'recommendation_label': rec_label,
        'candidate_name': candidate_name,
        'job_title': job_title,
        'match_score': match_score,
        'voice_score': voice_score,
        'assessment_score': assessment_score,
        'session_status': session_status,
        'strengths': strengths,
        'risks': risks,
        'questions': questions,
    }

    summary_html = render_to_string(
        'recruitment/ai_interview_report.html',
        {'report': summary_json},
    )

    return {'summary_json': summary_json, 'summary_html': summary_html}
