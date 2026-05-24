"""OSS voice answer scoring via embedding similarity."""

from __future__ import annotations

from recruitment.embeddings import encode_texts


def score_answer(ideal_answer: str, transcript: str) -> dict:
    transcript = (transcript or '').strip()
    ideal = (ideal_answer or '').strip()
    if not transcript:
        return {'score_percent': 0.0, 'feedback': 'No answer detected.'}
    if not ideal:
        return {'score_percent': 50.0, 'feedback': 'Answer recorded (no rubric).'}

    vectors = encode_texts([ideal[:4000], transcript[:4000]])
    sim = float((vectors[0] * vectors[1]).sum())
    score = max(0.0, min(100.0, sim * 100))

    if score >= 75:
        feedback = 'Strong match'
    elif score >= 50:
        feedback = 'Partial match'
    else:
        feedback = 'Weak match'

    return {'score_percent': round(score, 1), 'feedback': feedback}
