import re
from datetime import date, timedelta
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
    iso_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if iso_match:
        return iso_match.group(0)

    slash_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", text)
    if slash_match:
        day, month, year = slash_match.groups()
        normalized_year = int(year) + 2000 if len(year) == 2 else int(year)
        try:
            return date(normalized_year, int(month), int(day)).isoformat()
        except ValueError:
            return slash_match.group(0)

    lowered = text.lower()
    today = date.today()
    relative_deadlines = {
        "today": today,
        "aujourd'hui": today,
        "tomorrow": today + timedelta(days=1),
        "demain": today + timedelta(days=1),
        "this week": today + timedelta(days=5),
        "cette semaine": today + timedelta(days=5),
    }
    for phrase, normalized_date in relative_deadlines.items():
        if phrase in lowered:
            return normalized_date.isoformat()
    return None


def _extract_actor(text: str) -> Optional[str]:
    patterns = [
        r"(?im)^(?:from|de|par)\s*:\s*([^\n<]+)",
        r"\b(?:from|de|par)\s+([A-Z][a-zA-Z-]+(?:\s+[A-Z][a-zA-Z-]+){0,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            actor = re.sub(r"\s+", " ", match.group(1)).strip(" -,:;.")
            if actor:
                return actor
    return None


def _extract_subject(text: str) -> str:
    subject_match = re.search(r"(?im)^(?:subject|objet)\s*:\s*(.+)$", text)
    if subject_match:
        return subject_match.group(1).strip()[:120]

    non_empty_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if non_empty_lines:
        first_line = re.sub(r"^(?:re|fwd)\s*:\s*", "", non_empty_lines[0], flags=re.IGNORECASE)
        return first_line[:120]
    return "Demande sans sujet explicite"


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


def _detect_channel(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    if "@" in text or "subject:" in text.lower() or "objet:" in text.lower():
        return "email"
    return "text"


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
            channel=str(llm_payload.get("channel", _detect_channel(text))),
            tone=str(llm_payload.get("tone", _extract_tone(text))),
        )
    return ExtractedFields(
        priority=_detect_priority(text),
        subject=_extract_subject(text),
        deadline=_extract_deadline(text),
        actor=_extract_actor(text),
        action_requested=_extract_action(text),
        channel=_detect_channel(text),
        tone=_extract_tone(text),
    )
