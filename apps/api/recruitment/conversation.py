"""Conversation orchestration for low-latency AI interviews."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from django.utils import timezone

from recruitment.ai_client import generate_conversation_message
from recruitment.audio_provider_xyz import AudioProviderError, XyzAudioProvider
from recruitment.interview_manager import InterviewManager
from recruitment.live_events import emit_session_state, emit_transcript_segment
from recruitment.models import AiInterviewQuestion, AiInterviewSession, CandidateLiveResponse

SILENCE_PROMPT_TEXT = 'Would you like to skip this question, or should I repeat it?'
WRAP_UP_TEXT = (
    'Thank you for your time. We have completed all the structured evaluation questions. '
    'Our talent acquisition team will contact you shortly.'
)


@dataclass
class TurnEnvelope:
    question: AiInterviewQuestion
    ask_text: str
    tts_audio: bytes | None
    tts_mime: str
    silence_timeout_seconds: int


class ConversationManager:
    def __init__(self, silence_timeout_seconds: int = 5):
        self.interview_manager = InterviewManager(silence_timeout_seconds=silence_timeout_seconds)
        self.audio = XyzAudioProvider.from_settings()
        self.silence_timeout_seconds = self.interview_manager.silence_timeout_seconds

    def _session(self, session_id: str) -> AiInterviewSession:
        return AiInterviewSession.objects.select_related('candidate', 'job').get(pk=session_id)

    def start_turn(self, session_id: str) -> TurnEnvelope | None:
        session = self._session(session_id)
        question = session.questions.filter(answered_at__isnull=True).order_by('order').first()
        if not question:
            return None
        ask_text = self.build_ask_message(session, question)
        tts_audio, tts_mime = self.stream_question_tts(ask_text)
        emit_transcript_segment(
            session.id,
            speaker='AI',
            text=ask_text,
            question_order=question.order,
            is_final=True,
        )
        emit_session_state(
            session.id,
            status=session.status,
            current_question_index=question.order,
            phase='question',
        )
        return TurnEnvelope(
            question=question,
            ask_text=ask_text,
            tts_audio=tts_audio,
            tts_mime=tts_mime,
            silence_timeout_seconds=self.silence_timeout_seconds,
        )

    def build_ask_message(self, session: AiInterviewSession, question: AiInterviewQuestion) -> str:
        prompt = generate_conversation_message(
            question_text=question.question_text,
            candidate_name=f'{session.candidate.first_name} {session.candidate.last_name}',
            job_title=session.job.title,
            context='interviewer_turn',
        )
        return (prompt or question.question_text or '').strip()[:1200] or question.question_text

    def stream_question_tts(self, ask_text: str) -> tuple[bytes | None, str]:
        try:
            audio, mime = asyncio.run(self.audio.synthesize_tts(ask_text, voice='astra'))
            return audio, mime
        except AudioProviderError:
            return None, 'audio/mpeg'

    def stream_candidate_stt(self, audio_bytes: bytes, filename: str = 'answer.webm') -> dict:
        return asyncio.run(self.audio.transcribe_audio(audio_bytes, filename=filename))

    def handle_silence_timeout(self) -> dict:
        turn_decision = asyncio.run(self.interview_manager.monitor_turn_timeout())
        return {'action': turn_decision.action, 'prompt': turn_decision.prompt or SILENCE_PROMPT_TEXT}

    def resolve_repeat_skip(self, candidate_reply: str) -> str:
        decision = self.interview_manager.decide_repeat_or_skip(candidate_reply)
        return decision.action

    def finalize_turn(
        self,
        session: AiInterviewSession,
        question: AiInterviewQuestion,
        transcript_text: str,
        *,
        status: str = CandidateLiveResponse.STATUS_ANSWERED,
        repeated_count: int = 0,
        silence_seconds: int = 0,
    ) -> CandidateLiveResponse:
        return asyncio.run(
            self.interview_manager.record_live_transcript(
                session,
                question,
                transcript_text,
                status=status,
                repeated_count=repeated_count,
                silence_seconds=silence_seconds,
            )
        )

    def play_closing_and_request_feedback(self, session_id: str) -> dict:
        session = self._session(session_id)
        audio_bytes, mime = self.stream_question_tts(WRAP_UP_TEXT)
        emit_transcript_segment(session.id, speaker='AI', text=WRAP_UP_TEXT, is_final=True)
        emit_session_state(session.id, status=session.status, phase='completed')
        return {
            'wrap_up_text': WRAP_UP_TEXT,
            'tts_audio': audio_bytes,
            'tts_mime': mime,
            'feedback_required': True,
            'completed_at': timezone.now().isoformat(),
        }
