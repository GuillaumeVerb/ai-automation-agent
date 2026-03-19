import json
from typing import Any, Dict, Optional

import requests

from app.core.config import get_settings


settings = get_settings()


def _base_headers(request_id: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    if request_id:
        headers["X-Client-Request-Id"] = request_id
    return headers


def _extract_output_text(payload: dict) -> Optional[str]:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                text_value = content.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    return text_value
            if content.get("type") == "refusal":
                return None
    return None


def _responses_payload(system_prompt: str, user_prompt: str) -> dict:
    return {
        "model": settings.llm_model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
    }


def llm_available() -> bool:
    return settings.llm_enabled and bool(settings.llm_api_key.strip())


def complete_json(system_prompt: str, user_prompt: str, schema_name: str, schema: dict, request_id: Optional[str] = None) -> Optional[dict]:
    if not llm_available():
        return None

    payload = _responses_payload(system_prompt, user_prompt)
    payload["text"] = {
        "format": {
            "type": "json_schema",
            "name": schema_name,
            "strict": True,
            "schema": schema,
        }
    }
    try:
        response = requests.post(
            f"{settings.llm_base_url.rstrip('/')}/responses",
            headers=_base_headers(request_id),
            json=payload,
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
        content = _extract_output_text(response.json())
        return json.loads(content) if content else None
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError, TypeError):
        return None


def complete_text(system_prompt: str, user_prompt: str, request_id: Optional[str] = None) -> Optional[str]:
    if not llm_available():
        return None

    payload = _responses_payload(system_prompt, user_prompt)
    try:
        response = requests.post(
            f"{settings.llm_base_url.rstrip('/')}/responses",
            headers=_base_headers(request_id),
            json=payload,
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
        return _extract_output_text(response.json())
    except (requests.RequestException, KeyError, IndexError, TypeError):
        return None
