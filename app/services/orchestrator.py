import json
import time
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session

from app.models.run import Run
from app.models.schemas import Explainability, RunCreate, RunSummaryResponse, TimelineEvent
from app.services.classifier import classify_request
from app.services.email_generator import generate_email_reply
from app.services.extractor import extract_fields
from app.services.persistence import create_run_record, get_preference_hints
from app.services.preprocess import preprocess_text
from app.services.report_generator import generate_report
from app.services.scorer import compute_automation_score
from app.services.summarizer import summarize_request


def _append_event(events: List[TimelineEvent], step: str, detail: str) -> None:
    events.append(
        TimelineEvent(
            step=step,
            status="completed",
            detail=detail,
            timestamp=datetime.now(timezone.utc),
        )
    )


def _select_strategy(
    category: str,
    action_requested: str,
    risk_level: str,
    mode: str,
    preferred_output: Optional[str] = None,
) -> tuple[list[str], str]:
    strategy = ["summarize"]
    output_type = "summary"
    if preferred_output == "email_reply":
        strategy.append("generate_email_reply")
        output_type = "email_reply"
    elif preferred_output == "report":
        strategy.append("generate_report")
        output_type = "report"
    elif category in {"support", "commercial"} or action_requested == "prepare_reply":
        strategy.append("generate_email_reply")
        output_type = "email_reply"
    elif category == "reporting" or action_requested == "prepare_report":
        strategy.append("generate_report")
        output_type = "report"
    else:
        strategy.append("generate_report")
        output_type = "report"

    if risk_level != "low" or mode != "suggestion":
        strategy.append("human_review")
    strategy.append("log_run")
    return strategy, output_type


def create_run(session: Session, payload: RunCreate) -> tuple[Run, RunSummaryResponse]:
    started = time.perf_counter()
    timeline: List[TimelineEvent] = []

    clean_text, request_id = preprocess_text(payload.text)
    _append_event(timeline, "preprocess", "Input nettoye et request_id genere.")

    category, confidence, rationale, signals = classify_request(clean_text, request_id=request_id)
    _append_event(timeline, "classification", f"Demande classee en {category} avec confiance {confidence}.")

    extracted_fields = extract_fields(clean_text, request_id=request_id)
    _append_event(timeline, "extraction", "Champs metier extraits au format structure.")

    summary = summarize_request(clean_text, request_id=request_id)
    _append_event(timeline, "summary", "Resume concis genere.")

    score = compute_automation_score(category, confidence, extracted_fields.priority, payload.mode, request_id=request_id)
    strategy, output_type = _select_strategy(
        category,
        extracted_fields.action_requested,
        score.risk_level,
        payload.mode,
        payload.preferred_output,
    )
    _append_event(timeline, "routing", f"Strategie retenue: {', '.join(strategy)}.")

    if output_type == "email_reply":
        generated_output = generate_email_reply(clean_text, extracted_fields, request_id=request_id)
    else:
        generated_output = generate_report(clean_text, extracted_fields, request_id=request_id)
    _append_event(timeline, "generation", f"Sortie de type {output_type} generee.")

    preference_hints = get_preference_hints(session, category)
    _append_event(timeline, "review", "Sortie envoyee en validation humaine.")
    _append_event(timeline, "persistence", "Run journalise en base.")

    explainability = Explainability(
        category=category,
        confidence=confidence,
        signals=signals or ["general_request"],
        strategy=strategy,
        rationale=rationale,
    )

    latency_ms = int((time.perf_counter() - started) * 1000)
    estimated_cost = round(0.0004 + len(clean_text) / 100000, 5)

    run = Run(
        request_id=request_id,
        input_text=clean_text,
        input_type=payload.input_type,
        mode=payload.mode,
        category=category,
        confidence=confidence,
        rationale=rationale,
        extracted_fields_json=extracted_fields.model_dump_json(),
        summary=summary,
        generated_output=generated_output,
        output_type=output_type,
        strategy_json=json.dumps(strategy),
        explainability_json=explainability.model_dump_json(),
        timeline_json=json.dumps([event.model_dump(mode="json") for event in timeline], default=str),
        automation_score=score.automation_score,
        risk_level=score.risk_level,
        estimated_time_saved_minutes=score.estimated_time_saved_minutes,
        autonomy_recommendation=score.autonomy_recommendation,
        status="pending_review",
        latency_ms=latency_ms,
        estimated_cost=estimated_cost,
        used_preferences_json=json.dumps(preference_hints),
    )
    stored = create_run_record(session, run)
    response = RunSummaryResponse(
        run_id=stored.id,
        category=stored.category,
        confidence=stored.confidence,
        summary=stored.summary,
        strategy=json.loads(stored.strategy_json),
        automation_score=stored.automation_score,
        risk_level=stored.risk_level,
    )
    return stored, response


def regenerate_run(
    session: Session,
    source_run: Run,
    strategy_hint: Optional[str] = None,
    preferred_output: Optional[str] = None,
) -> tuple[Run, RunSummaryResponse]:
    mode = source_run.mode
    requested_output = preferred_output
    if not requested_output and strategy_hint:
        if "email" in strategy_hint.lower():
            requested_output = "email_reply"
        elif "report" in strategy_hint.lower():
            requested_output = "report"

    payload = RunCreate(
        text=source_run.input_text,
        input_type=source_run.input_type,
        mode=mode,
        preferred_output=requested_output,
    )
    return create_run(session, payload)
