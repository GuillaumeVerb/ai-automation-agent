import json
import time
from typing import Dict, Optional

from sqlmodel import Session

from app.models.run import Run
from app.models.schemas import ExtractedFields, RunCreate, RunSummaryResponse
from app.services.classifier import classify_request
from app.services.email_generator import generate_email_reply
from app.services.explainability import build_explainability
from app.services.extractor import extract_fields
from app.services.persistence import create_run_record, get_preference_hints, get_preference_map
from app.services.preprocess import preprocess_text
from app.services.report_generator import generate_report
from app.services.scorer import compute_automation_score
from app.services.summarizer import summarize_request
from app.services.timeline import TimelineTracker


def _select_strategy(
    category: str,
    action_requested: str,
    risk_level: str,
    recommended_mode: str,
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
    else:
        strategy.append("generate_report")
        output_type = "report"

    if risk_level != "low" or recommended_mode != "low_risk_auto":
        strategy.append("human_review")
    strategy.append("log_run")
    return strategy, output_type


def _apply_preference_hints(extracted_fields: ExtractedFields, preference_map: Dict[str, str], category: str) -> ExtractedFields:
    tone_key = f"tone:{category}"
    if tone_key in preference_map:
        return extracted_fields.model_copy(update={"tone": preference_map[tone_key]})
    return extracted_fields


def create_run(session: Session, payload: RunCreate) -> tuple[Run, RunSummaryResponse]:
    started = time.perf_counter()
    timeline = TimelineTracker()
    timeline.add_instant("input_received", "Input recu par l'API.", payload.input_type)

    preprocess_started = time.perf_counter()
    clean_text, request_id = preprocess_text(payload.text)
    timeline.add_step("preprocessed", "Input nettoye et request_id genere.", request_id, preprocess_started)

    classification_started = time.perf_counter()
    category, confidence, rationale, signals = classify_request(clean_text, request_id=request_id)
    timeline.add_step(
        "classified",
        f"Demande classee en {category} avec confiance {confidence}.",
        f"{category} ({confidence:.2f})",
        classification_started,
    )

    extracted_fields_started = time.perf_counter()
    extracted_fields = extract_fields(clean_text, request_id=request_id)
    timeline.add_step(
        "extracted",
        "Champs metier extraits au format structure.",
        f"priorite={extracted_fields.priority}, action={extracted_fields.action_requested}",
        extracted_fields_started,
    )

    preference_map = get_preference_map(session, category)
    extracted_fields = _apply_preference_hints(extracted_fields, preference_map, category)
    preference_hints = get_preference_hints(session, category)

    summary = summarize_request(clean_text, request_id=request_id)

    generation_started = time.perf_counter()
    score = compute_automation_score(category, confidence, extracted_fields, payload.mode, request_id=request_id)
    strategy, output_type = _select_strategy(
        category,
        extracted_fields.action_requested,
        score.risk_level,
        score.autonomy_mode,
        payload.preferred_output,
    )
    if output_type == "email_reply":
        generated_output = generate_email_reply(clean_text, extracted_fields, request_id=request_id)
    else:
        generated_output = generate_report(clean_text, extracted_fields, request_id=request_id)
    timeline.add_step(
        "generated",
        f"Sortie de type {output_type} generee.",
        output_type,
        generation_started,
    )

    scoring_started = time.perf_counter()
    explainability = build_explainability(
        category=category,
        confidence=confidence,
        signals=signals,
        strategy=strategy,
        classifier_rationale=rationale,
        risk_level=score.risk_level,
        requested_mode=payload.mode,
        recommended_mode=score.autonomy_mode,
    )
    timeline.add_step(
        "scored",
        "Score d'automatisation et recommandation d'autonomie calcules.",
        f"score={score.global_score}, mode={score.autonomy_mode}",
        scoring_started,
    )

    timeline.add_instant(
        "reviewed",
        "Sortie envoyee en validation humaine.",
        "Validation en attente" if score.autonomy_mode != "low_risk_auto" else "Mode auto simule visible",
        status="pending",
    )
    timeline.add_instant("saved", "Run journalise en base.", "Persisted")

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
        timeline_json=json.dumps([event.model_dump(mode="json") for event in timeline.events], default=str),
        automation_score=score.global_score,
        score_breakdown_json=json.dumps(score.model_dump()),
        risk_level=score.risk_level,
        autonomy_mode=score.autonomy_mode,
        estimated_time_saved_minutes=score.estimated_time_saved_minutes,
        autonomy_recommendation=score.autonomy_mode,
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
    requested_output = preferred_output
    if not requested_output and strategy_hint:
        if "email" in strategy_hint.lower():
            requested_output = "email_reply"
        elif "report" in strategy_hint.lower():
            requested_output = "report"

    payload = RunCreate(
        text=source_run.input_text,
        input_type=source_run.input_type,
        mode=source_run.mode,
        preferred_output=requested_output,
    )
    return create_run(session, payload)
