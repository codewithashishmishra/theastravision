"""Async interview turn state manager for repeat/skip flow."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from recruitment.models import AiInterviewQuestion, AiInterviewSession, CandidateLiveResponse


@dataclass
class TurnDecision:
    action: str
    prompt: str = ''


class InterviewManager:
    """Coordinates silence timeout and repeat/skip branching."""

    def __init__(self, silence_timeout_seconds: int = 5):
        self.silence_timeout_seconds = max(4, min(5, int(silence_timeout_seconds)))

    async def ask_next_question(self, session: AiInterviewSession) -> AiInterviewQuestion | None:
        return session.questions.filter(answered_at__isnull=True).order_by('order').first()

    async def monitor_turn_timeout(self) -> TurnDecision:
        await asyncio.sleep(self.silence_timeout_seconds)
        return TurnDecision(
            action='timeout_prompt',
            prompt='Would you like to skip this question, or should I repeat it?',
        )

    async def handle_repeat_or_skip(self, candidate_reply: str) -> TurnDecision:
        normalized = (candidate_reply or '').strip().lower()
        if 'repeat' in normalized:
            return TurnDecision(action='repeat')
        if 'skip' in normalized or not normalized:
            return TurnDecision(action='skip')
        return TurnDecision(action='continue')

    def decide_repeat_or_skip(self, candidate_reply: str) -> TurnDecision:
        normalized = (candidate_reply or '').strip().lower()
        if 'repeat' in normalized:
            return TurnDecision(action='repeat')
        if 'skip' in normalized or not normalized:
            return TurnDecision(action='skip')
        return TurnDecision(action='continue')

    async def record_live_transcript(
        self,
        session: AiInterviewSession,
        question: AiInterviewQuestion,
        transcript_text: str,
        *,
        status: str = CandidateLiveResponse.STATUS_ANSWERED,
        repeated_count: int = 0,
        silence_seconds: int = 0,
    ) -> CandidateLiveResponse:
        prebaked = session.prebaked_questions.filter(order=question.order).first()
        return CandidateLiveResponse.objects.create(
            tenant_id=session.tenant_id,
            candidate=session.candidate,
            session=session,
            interview_question=question,
            prebaked_question=prebaked,
            question_order=question.order,
            transcript_text=transcript_text or '',
            status=status,
            repeated_count=repeated_count,
            silence_seconds=silence_seconds,
        )
