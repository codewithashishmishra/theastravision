import json
import os
from typing import Any

from fastapi import Header, HTTPException

from config import OPENAI_API_KEY, OPENAI_MODEL


def resolve_credentials(
    x_openai_api_key: str | None = Header(default=None),
    x_openai_model: str | None = Header(default=None),
) -> tuple[str, str]:
    api_key = x_openai_api_key or os.environ.get('OPENAI_API_KEY') or OPENAI_API_KEY
    model = x_openai_model or os.environ.get('OPENAI_MODEL') or OPENAI_MODEL
    if not api_key:
        raise HTTPException(status_code=503, detail='OpenAI API key not configured.')
    return api_key, model


def chat_json(api_key: str, model: str, system: str, user: str) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        response_format={'type': 'json_object'},
    )
    content = response.choices[0].message.content or '{}'
    return json.loads(content)


def chat_text(api_key: str, model: str, system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
    )
    return response.choices[0].message.content or ''
