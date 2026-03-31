import json
import time
from typing import Dict, Optional
from uuid import uuid4

from sqlmodel import Session

from app.db.session import engine
from app.models.run import Run
from app.models.schemas import Explainability, ExtractedFields, RunCreate, RunSummaryResponse, ScoreResult, TimelineEvent
from app.services.classifier import classify_request
from app.services.email_generator import generate_email_reply
from app.services.explainability import build_explainability
from app.services.extractor import extract_fields
from app.services.persistence import append_timeline_event, create_run_record, get_preference_hints, get_preference_map, get_run
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


def _placeholder_extracted_fields() -> ExtractedFields:
    return ExtractedFields(
        priority="low",
        subject="Demande en cours de traitement",
        deadline=None,
        actor=None,
        action_requested="assess_request",
        channel="text",
        tone="neutral",
    )


def _placeholder_explainability(requested_mode: str) -> Explainability:
    return Explainability(
        category="autre",
        confidence=0.0,
        signals=["run_processing"],
        strategy=[],
        rationale="Run initialise et en cours de traitement.",
        risk_level="low",
    )


def _placeholder_score(requested_mode: str) -> ScoreResult:
    return ScoreResult(
        global_score=0,
        confidence_score=0,
        risk_score=0,
        completeness_score=0,
        risk_level="low",
        autonomy_mode=requested_mode,
        estimated_time_saved_minutes=0,
        rationale="Score non disponible tant que le run est en cours de traitement.",
    )


def _build_step_event(
    step: str,
    detail: str,
    output_summary: str,
    started_at: Optional[float] = None,
    status: str = "completed",
) -> TimelineEvent:
    duration_ms = max(0, int((time.perf_counter() - started_at) * 1000)) if started_at is not None else 0
    return TimelineEvent(
        step=step,
        status=status,
        detail=detail,
        timestamp=time_to_utc_now(),
        duration_ms=duration_ms,
        output_summary=output_summary,
    )


def time_to_utc_now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def _processing_summary_response(run: Run) -> RunSummaryResponse:
    return RunSummaryResponse(
        run_id=run.id,
        category=run.category,
        confidence=run.confidence,
        summary=run.summary,
        strategy=json.loads(run.strategy_json),
        automation_score=run.automation_score,
        risk_level=run.risk_level,
    )


def initialize_run(session: Session, payload: RunCreate) -> tuple[Run, RunSummaryResponse]:
    timeline = TimelineTracker()
    timeline.add_instant("input_received", "Input recu par l'API.", payload.input_type)

    placeholder_fields = _placeholder_extracted_fields()
    placeholder_explainability = _placeholder_explainability(payload.mode)
    placeholder_score = _placeholder_score(payload.mode)
    run = Run(
        request_id=f"req_{uuid4().hex[:12]}",
        input_text=payload.text,
        input_type=payload.input_type,
        mode=payload.mode,
        category="autre",
        confidence=0.0,
        rationale="Run initialise et en cours de traitement.",
        extracted_fields_json=placeholder_fields.model_dump_json(),
        summary="Traitement en cours...",
        generated_output="",
        output_type=payload.preferred_output or "summary",
        strategy_json=json.dumps([]),
        explainability_json=placeholder_explainability.model_dump_json(),
        timeline_json=json.dumps([event.model_dump(mode="json") for event in timeline.events], default=str),
        automation_score=0,
        score_breakdown_json=json.dumps(placeholder_score.model_dump()),
        risk_level="low",
        autonomy_mode=payload.mode,
        estimated_time_saved_minutes=0,
        autonomy_recommendation=payload.mode,
        status="processing",
        latency_ms=0,
        estimated_cost=0.0,
        used_preferences_json="[]",
    )
    stored = create_run_record(session, run)
    return stored, _processing_summary_response(stored)


def process_initialized_run(session: Session, run: Run, payload: RunCreate) -> tuple[Run, RunSummaryResponse]:
    started = time.perf_counter()

    preprocess_started = time.perf_counter()
    clean_text, request_id = preprocess_text(payload.text)
    run.request_id = request_id
    run.input_text = clean_text
    session.add(run)
    session.commit()
    session.refresh(run)
    run = append_timeline_event(
        session,
        run,
        _build_step_event("preprocessed", "Input nettoye et request_id genere.", request_id, preprocess_started),
    )

    classification_started = time.perf_counter()
    category, confidence, rationale, signals = classify_request(clean_text, request_id=request_id)
    run.category = category
    run.confidence = confidence
    run.rationale = rationale
    session.add(run)
    session.commit()
    session.refresh(run)
    run = append_timeline_event(
        session,
        run,
        _build_step_event(
            "classified",
            f"Demande classee en {category} avec confiance {confidence}.",
            f"{category} ({confidence:.2f})",
            classification_started,
        ),
    )

    extracted_fields_started = time.perf_counter()
    extracted_fields = extract_fields(clean_text, request_id=request_id)

    preference_map = get_preference_map(session, category)
    extracted_fields = _apply_preference_hints(extracted_fields, preference_map, category)
    preference_hints = get_preference_hints(session, category)
    run.extracted_fields_json = extracted_fields.model_dump_json()
    run.used_preferences_json = json.dumps(preference_hints)
    session.add(run)
    session.commit()
    session.refresh(run)
    run = append_timeline_event(
        session,
        run,
        _build_step_event(
            "extracted",
            "Champs metier extraits au format structure.",
            f"priorite={extracted_fields.priority}, action={extracted_fields.action_requested}",
            extracted_fields_started,
        ),
    )

    summary = summarize_request(clean_text, request_id=request_id)
    run.summary = summary
    session.add(run)
    session.commit()
    session.refresh(run)

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
        generated_output = generate_email_reply(clean_text, extracted_fields, category, request_id=request_id)
    else:
        generated_output = generate_report(clean_text, extracted_fields, category, request_id=request_id)
    run.output_type = output_type
    run.generated_output = generated_output
    run.strategy_json = json.dumps(strategy)
    session.add(run)
    session.commit()
    session.refresh(run)
    run = append_timeline_event(
        session,
        run,
        _build_step_event(
            "generated",
            f"Sortie de type {output_type} generee.",
            output_type,
            generation_started,
        ),
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
    run.explainability_json = explainability.model_dump_json()
    run.automation_score = score.global_score
    run.score_breakdown_json = json.dumps(score.model_dump())
    run.risk_level = score.risk_level
    run.autonomy_mode = score.autonomy_mode
    run.estimated_time_saved_minutes = score.estimated_time_saved_minutes
    run.autonomy_recommendation = score.autonomy_mode
    session.add(run)
    session.commit()
    session.refresh(run)
    run = append_timeline_event(
        session,
        run,
        _build_step_event(
            "scored",
            "Score d'automatisation et recommandation d'autonomie calcules.",
            f"score={score.global_score}, mode={score.autonomy_mode}",
            scoring_started,
        ),
    )

    latency_ms = int((time.perf_counter() - started) * 1000)
    estimated_cost = round(0.0004 + len(clean_text) / 100000, 5)
    run.status = "pending_review"
    run.latency_ms = latency_ms
    run.estimated_cost = estimated_cost
    session.add(run)
    session.commit()
    session.refresh(run)
    run = append_timeline_event(
        session,
        run,
        _build_step_event(
            "reviewed",
            "Sortie envoyee en validation humaine.",
            "Validation en attente" if score.autonomy_mode != "low_risk_auto" else "Mode auto simule visible",
            status="pending",
        ),
    )
    run = append_timeline_event(session, run, _build_step_event("saved", "Run journalise en base.", "Persisted"))

    response = RunSummaryResponse(
        run_id=run.id,
        category=run.category,
        confidence=run.confidence,
        summary=run.summary,
        strategy=json.loads(run.strategy_json),
        automation_score=run.automation_score,
        risk_level=run.risk_level,
    )
    return run, response


def create_run(session: Session, payload: RunCreate) -> tuple[Run, RunSummaryResponse]:
    run, _ = initialize_run(session, payload)
    return process_initialized_run(session, run, payload)


def process_run_async(run_id: str, payload_data: dict) -> None:
    payload = RunCreate(**payload_data)
    with Session(engine) as session:
        run = get_run(session, run_id)
        if not run:
            return
        try:
            process_initialized_run(session, run, payload)
        except Exception as exc:
            run.status = "failed"
            run.rationale = f"Le run a echoue pendant le traitement: {exc}"
            session.add(run)
            session.commit()


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
