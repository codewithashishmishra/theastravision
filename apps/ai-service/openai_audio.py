import tempfile

from config import OPENAI_STT_MODEL, OPENAI_TTS_MODEL, OPENAI_TTS_VOICE


def transcribe_audio(api_key: str, audio_bytes: bytes, filename: str = 'audio.webm') -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    suffix = '.webm' if 'webm' in (filename or '') else '.wav'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    with open(tmp_path, 'rb') as audio_file:
        result = client.audio.transcriptions.create(
            model=OPENAI_STT_MODEL,
            file=audio_file,
            response_format='verbose_json',
        )
    text = getattr(result, 'text', '') or ''
    lang = getattr(result, 'language', None) or 'en'
    return {'text': text.strip(), 'detected_language': lang}


def synthesize_speech(api_key: str, text: str) -> bytes:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.audio.speech.create(
        model=OPENAI_TTS_MODEL,
        voice=OPENAI_TTS_VOICE,
        input=text[:4096],
    )
    return response.content
