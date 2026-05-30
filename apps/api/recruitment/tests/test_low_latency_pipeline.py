from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from recruitment.conversation import ConversationManager
from recruitment.interview_manager import InterviewManager
from recruitment.services import _normalize_tier, build_semantic_interview_report


class InterviewManagerTests(SimpleTestCase):
    def test_decide_repeat_or_skip(self):
        manager = InterviewManager(silence_timeout_seconds=5)
        self.assertEqual(manager.decide_repeat_or_skip('repeat please').action, 'repeat')
        self.assertEqual(manager.decide_repeat_or_skip('skip').action, 'skip')
        self.assertEqual(manager.decide_repeat_or_skip('').action, 'skip')
        self.assertEqual(manager.decide_repeat_or_skip('continue').action, 'continue')


class RecruitmentLowLatencyLogicTests(SimpleTestCase):
    def test_normalize_tier_defaults_to_medium(self):
        self.assertEqual(_normalize_tier('LOW'), 'low')
        self.assertEqual(_normalize_tier('Extreme Hard'), 'extreme_hard')
        self.assertEqual(_normalize_tier('unknown-tier'), 'medium')

    @patch('recruitment.services.semantic_evaluate_answer')
    def test_semantic_report_contains_scored_turns(self, mock_eval):
        mock_eval.return_value = {
            'score_out_of_10': 8,
            'feedback': 'Solid answer.',
            'strengths': ['Clear basics'],
            'gaps': ['Could add trade-offs'],
        }
        q1 = SimpleNamespace(
            order=1,
            question_text='Explain indexing.',
            ideal_answer='Use selective indexes.',
            candidate_transcript='Use B-tree where needed.',
            skipped=False,
        )
        q2 = SimpleNamespace(
            order=2,
            question_text='What is CAP theorem?',
            ideal_answer='Consistency, Availability, Partition tolerance.',
            candidate_transcript='',
            skipped=True,
        )
        questions = SimpleNamespace(all=lambda: SimpleNamespace(order_by=lambda *_: [q1, q2]))
        session = SimpleNamespace(
            id='s1',
            candidate_id='c1',
            questions=questions,
        )
        payload = build_semantic_interview_report(session)
        self.assertEqual(len(payload['turns']), 2)
        self.assertEqual(payload['turns'][0]['score_out_of_10'], 8)
        self.assertEqual(payload['turns'][1]['status'], 'skipped')

    @patch('recruitment.conversation.generate_conversation_message')
    def test_conversation_message_fallback(self, mock_message):
        mock_message.return_value = 'Hi Ashish, let us begin.'
        manager = ConversationManager(silence_timeout_seconds=4)
        session = SimpleNamespace(
            candidate=SimpleNamespace(first_name='Ashish', last_name='Mishra'),
            job=SimpleNamespace(title='Python Engineer'),
        )
        question = SimpleNamespace(question_text='Explain ACID properties.')
        ask = manager.build_ask_message(session, question)
        self.assertIn('let us begin', ask.lower())
