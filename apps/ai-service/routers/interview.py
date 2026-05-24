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
