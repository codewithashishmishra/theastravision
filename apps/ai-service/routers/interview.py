from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from openai_audio import synthesize_speech, transcribe_audio
from openai_client import chat_json, resolve_credentials

router = APIRouter(prefix='/api/v1/ai', tags=['interview'])


class GenerateQuestionsRequest(BaseModel):
    job_title: str
    job_description: str
    resume_text: str
    count: int = 5


class GenerateAssessmentRequest(BaseModel):
    job_title: str
    job_description: str
    resume_text: str = ''
    count: int = 10


class TtsRequest(BaseModel):
    text: str
    voice: str = 'astra'


class CampaignBaselineQuestionsRequest(BaseModel):
    campaign_id: str | None = None
    job_title: str
    jd_text: str
    count: int = 5


class CandidateAdaptiveQuestionsRequest(BaseModel):
    candidate_id: str | None = None
    campaign_id: str | None = None
    job_title: str
    jd_text: str
    resume_text: str
    experience_summary: str = ''
    count: int = 5


class SemanticEvaluationRequest(BaseModel):
    question: str
    benchmark_answer: str
    candidate_answer: str


class ConversationMessageRequest(BaseModel):
    question_text: str
    candidate_name: str
    job_title: str
    context: str = 'interviewer_turn'


@router.post('/generate-questions')
async def generate_questions(
    request: GenerateQuestionsRequest,
    x_openai_api_key: str | None = Header(default=None),
    x_openai_model: str | None = Header(default=None),
):
    api_key, model = resolve_credentials(x_openai_api_key, x_openai_model)
    prompt = f"""Generate {request.count} interview questions mixing JD and resume.
Job: {request.job_title}
JD: {request.job_description[:6000]}
Resume: {request.resume_text[:6000]}

Return JSON: {{ "questions": [ {{ "question": "...", "ideal_answer": "...", "rubric": "..." }} ] }}
Do not include ideal answers in spoken form hints."""
    return chat_json(api_key, model, 'You create structured interview questions.', prompt)


@router.post('/recruitment/campaign-baseline-questions')
async def campaign_baseline_questions(
    request: CampaignBaselineQuestionsRequest,
    x_openai_api_key: str | None = Header(default=None),
    _x_openai_model: str | None = Header(default=None),
):
    api_key, _resolved_model = resolve_credentials(x_openai_api_key, None)
    prompt = f"""Generate exactly 5 foundational technical calibration interview questions.
Job title: {request.job_title}
JD text: {request.jd_text[:12000]}

Hard constraints:
- Return exactly 5 items.
- Focus only on technical calibration relevant to the role.
- Keep each ideal answer practical and benchmark-quality.

Return JSON:
{{
  "questions": [
    {{
      "question": "...",
      "ideal_answer": "...",
      "difficulty_tier": "medium"
    }}
  ]
}}"""
    return chat_json(api_key, 'gpt-5.4-mini', 'You generate strict JSON technical interview baselines.', prompt)


@router.post('/recruitment/candidate-adaptive-questions')
async def candidate_adaptive_questions(
    request: CandidateAdaptiveQuestionsRequest,
    x_openai_api_key: str | None = Header(default=None),
    _x_openai_model: str | None = Header(default=None),
):
    api_key, _resolved_model = resolve_credentials(x_openai_api_key, None)
    prompt = f"""Generate exactly 5 personalized interview questions for this candidate.
Job title: {request.job_title}
JD text: {request.jd_text[:10000]}
Resume text: {request.resume_text[:10000]}
Experience summary: {request.experience_summary[:2000]}

Hard constraints:
- Return exactly 5 items.
- Each item must include one tier from: low, medium, hard, extreme_hard.
- Cover at least 4 tiers across the 5 questions.
- Questions must be adaptive to the candidate profile.
- Include benchmark ideal answers.

Return JSON:
{{
  "questions": [
    {{
      "question": "...",
      "ideal_answer": "...",
      "difficulty_tier": "low"
    }}
  ]
}}"""
    return chat_json(api_key, 'gpt-5.4-mini', 'You generate personalized tiered interview questions in JSON.', prompt)


@router.post('/recruitment/semantic-evaluation')
async def semantic_evaluation(
    request: SemanticEvaluationRequest,
    x_openai_api_key: str | None = Header(default=None),
    _x_openai_model: str | None = Header(default=None),
):
    api_key, _resolved_model = resolve_credentials(x_openai_api_key, None)
    prompt = f"""Evaluate the candidate answer against the benchmark.
Question: {request.question[:3000]}
Benchmark answer: {request.benchmark_answer[:6000]}
Candidate answer: {request.candidate_answer[:6000]}

Return strict JSON:
{{
  "score_out_of_10": 0,
  "feedback": "clear concise feedback",
  "strengths": ["..."],
  "gaps": ["..."]
}}"""
    return chat_json(api_key, 'gpt-5.4-mini', 'You are a strict interview evaluator producing JSON only.', prompt)


@router.post('/recruitment/conversation-message')
async def conversation_message(
    request: ConversationMessageRequest,
    x_openai_api_key: str | None = Header(default=None),
    _x_openai_model: str | None = Header(default=None),
):
    api_key, _resolved_model = resolve_credentials(x_openai_api_key, None)
    prompt = f"""Create one short conversational interviewer line.
Candidate name: {request.candidate_name}
Job title: {request.job_title}
Context: {request.context}
Base interview question: {request.question_text}

Rules:
- Keep it concise and professional.
- Do not reveal ideal answers.
- Do not ask multiple new questions.

Return strict JSON:
{{
  "message": "single interviewer utterance"
}}"""
    return chat_json(
        api_key,
        'gpt-5.4-mini',
        'You are an AI interviewer creating concise spoken prompts.',
        prompt,
    )


@router.post('/generate-assessment')
async def generate_assessment(
    request: GenerateAssessmentRequest,
    x_openai_api_key: str | None = Header(default=None),
    x_openai_model: str | None = Header(default=None),
):
    api_key, model = resolve_credentials(x_openai_api_key, x_openai_model)
    prompt = f"""Create {request.count} MCQ questions for online assessment.
Job: {request.job_title}
JD: {request.job_description[:6000]}
Resume context: {request.resume_text[:4000]}

Return JSON: {{ "questions": [ {{ "prompt": "...", "options": {{ "A":"...", "B":"...", "C":"...", "D":"..." }}, "correct_option": "A" }} ] }}"""
    return chat_json(api_key, model, 'You write fair technical MCQ assessments.', prompt)


@router.post('/transcribe')
async def transcribe(
    audio: UploadFile = File(...),
    x_openai_api_key: str | None = Header(default=None),
    x_openai_model: str | None = Header(default=None),
):
    api_key, _model = resolve_credentials(x_openai_api_key, x_openai_model)
    content = await audio.read()
    raw = transcribe_audio(api_key, content, audio.filename or 'audio.webm')
    return {
        'text': raw['text'],
        'english_text': raw['text'],
        'detected_language': raw['detected_language'],
    }


@router.post('/tts')
async def text_to_speech(
    request: TtsRequest,
    x_openai_api_key: str | None = Header(default=None),
    x_openai_model: str | None = Header(default=None),
):
    api_key, _model = resolve_credentials(x_openai_api_key, x_openai_model)
    if not request.text.strip():
        raise HTTPException(status_code=400, detail='text required')
    audio = synthesize_speech(api_key, request.text[:2000])
    return Response(content=audio, media_type='audio/mpeg')
