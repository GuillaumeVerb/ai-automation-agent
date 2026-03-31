import json
from contextvars import ContextVar
from typing import Any, Dict, Optional

import requests

from app.core.config import get_settings


settings = get_settings()
_llm_trace: ContextVar[list[dict[str, str]]] = ContextVar("llm_trace", default=[])


def begin_llm_trace() -> None:
    _llm_trace.set([])


def _record_llm_event(task: str, status: str, detail: str) -> None:
    current = list(_llm_trace.get())
    current.append({"task": task, "status": status, "detail": detail})
    _llm_trace.set(current)


def consume_llm_trace() -> list[dict[str, str]]:
    current = list(_llm_trace.get())
    _llm_trace.set([])
    return current


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


def complete_json(
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    schema: dict,
    request_id: Optional[str] = None,
) -> Optional[dict]:
    task_name = schema_name
    if not llm_available():
        status = "provider_disabled" if not settings.llm_enabled else "provider_unconfigured"
        _record_llm_event(task_name, status, "LLM indisponible, fallback heuristique utilise.")
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
        if content:
            _record_llm_event(task_name, "provider_live", "Reponse provider recue.")
            return json.loads(content)
        _record_llm_event(task_name, "provider_empty", "Reponse provider vide, fallback heuristique active.")
        return None
    except requests.Timeout:
        _record_llm_event(task_name, "provider_timeout", "Timeout provider, fallback heuristique active.")
        return None
    except requests.RequestException as exc:
        _record_llm_event(task_name, "provider_error", f"Erreur provider: {exc.__class__.__name__}.")
        return None
    except (KeyError, IndexError, TypeError):
        _record_llm_event(task_name, "provider_invalid_payload", "Payload provider invalide, fallback heuristique active.")
        return None
    except json.JSONDecodeError:
        _record_llm_event(task_name, "provider_invalid_json", "JSON provider invalide, fallback heuristique active.")
        return None


def complete_text(
    system_prompt: str,
    user_prompt: str,
    request_id: Optional[str] = None,
    task_name: str = "text_completion",
) -> Optional[str]:
    if not llm_available():
        status = "provider_disabled" if not settings.llm_enabled else "provider_unconfigured"
        _record_llm_event(task_name, status, "LLM indisponible, fallback heuristique utilise.")
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
        content = _extract_output_text(response.json())
        if content:
            _record_llm_event(task_name, "provider_live", "Reponse provider recue.")
            return content
        _record_llm_event(task_name, "provider_empty", "Reponse provider vide, fallback heuristique active.")
        return None
    except requests.Timeout:
        _record_llm_event(task_name, "provider_timeout", "Timeout provider, fallback heuristique active.")
        return None
    except requests.RequestException as exc:
        _record_llm_event(task_name, "provider_error", f"Erreur provider: {exc.__class__.__name__}.")
        return None
    except (KeyError, IndexError, TypeError):
        _record_llm_event(task_name, "provider_invalid_payload", "Payload provider invalide, fallback heuristique active.")
        return None
