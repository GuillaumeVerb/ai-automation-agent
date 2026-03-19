import re
from typing import Optional

from app.models.schemas import ExtractedFields
from app.services.llm_engine import complete_json
from app.services.prompt_loader import load_prompt


PRIORITY_KEYWORDS = {
    "high": ["urgent", "asap", "critique", "bloquant", "today", "aujourd"],
    "medium": ["soon", "demain", "cette semaine", "important"],
}

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "subject": {"type": "string"},
        "deadline": {"type": ["string", "null"]},
        "actor": {"type": ["string", "null"]},
        "action_requested": {"type": "string", "enum": ["prepare_reply", "prepare_report", "triage_issue", "assess_request"]},
        "channel": {"type": "string", "enum": ["email", "text", "json"]},
        "tone": {"type": "string", "enum": ["urgent", "polite", "neutral"]},
    },
    "required": ["priority", "subject", "deadline", "actor", "action_requested", "channel", "tone"],
    "additionalProperties": False,
}


def _detect_priority(text: str) -> str:
    lowered = text.lower()
    for priority, keywords in PRIORITY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return priority
    return "low"


def _extract_deadline(text: str) -> Optional[str]:
    patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b(?:today|tomorrow|demain|aujourd'hui|this week)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def _extract_actor(text: str) -> Optional[str]:
    match = re.search(r"\b(?:from|de|par)\s+([A-Z][a-zA-Z-]+)", text)
    return match.group(1) if match else None


def _extract_subject(text: str) -> str:
    sentence = re.split(r"[.!?]", text.strip())[0]
    return sentence[:120] if sentence else "Demande sans sujet explicite"


def _extract_action(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["reply", "reponse", "respond", "email"]):
        return "prepare_reply"
    if any(word in lowered for word in ["report", "rapport", "dashboard", "kpi"]):
        return "prepare_report"
    if any(word in lowered for word in ["bug", "issue", "incident", "ticket"]):
        return "triage_issue"
    return "assess_request"


def _extract_tone(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["urgent", "asap", "immediately", "critique"]):
        return "urgent"
    if any(word in lowered for word in ["thanks", "merci", "please", "svp"]):
        return "polite"
    return "neutral"


def extract_fields(text: str, request_id: str = "") -> ExtractedFields:
    llm_payload = complete_json(
        load_prompt("extraction"),
        text,
        schema_name="request_extraction",
        schema=EXTRACTION_SCHEMA,
        request_id=request_id,
    )
    if llm_payload:
        return ExtractedFields(
            priority=str(llm_payload.get("priority", "low")),
            subject=str(llm_payload.get("subject", _extract_subject(text))),
            deadline=llm_payload.get("deadline"),
            actor=llm_payload.get("actor"),
            action_requested=str(llm_payload.get("action_requested", _extract_action(text))),
            channel=str(llm_payload.get("channel", "email" if "@" in text or "subject:" in text.lower() else "text")),
            tone=str(llm_payload.get("tone", _extract_tone(text))),
        )
    return ExtractedFields(
        priority=_detect_priority(text),
        subject=_extract_subject(text),
        deadline=_extract_deadline(text),
        actor=_extract_actor(text),
        action_requested=_extract_action(text),
        channel="email" if "@" in text or "subject:" in text.lower() else "text",
        tone=_extract_tone(text),
    )
