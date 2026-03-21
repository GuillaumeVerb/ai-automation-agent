import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlmodel import Session, select

from app.models.feedback import Feedback
from app.models.preference import Preference
from app.models.run import Run
from app.models.timeline_event import TimelineEventRecord
from app.models.schemas import FeedbackCreate, FeedbackRead, MetricsResponse, RunDetailResponse, ScoreBreakdown


def _parse_event_timestamp(raw_timestamp: str) -> datetime:
    return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))


def create_run_record(session: Session, run: Run) -> Run:
    session.add(run)
    session.flush()
    _persist_timeline_records(session, run)
    session.commit()
    session.refresh(run)
    return run


def list_runs(session: Session, limit: int = 50) -> List[Run]:
    statement = select(Run).order_by(Run.created_at.desc()).limit(limit)
    return list(session.exec(statement))


def get_run(session: Session, run_id: str) -> Optional[Run]:
    return session.get(Run, run_id)


def _update_human_validation_timeline(run: Run, status: str, detail: str, output_summary: str) -> None:
    timeline = json.loads(run.timeline_json)
    for event in timeline:
        if event["step"] == "reviewed":
            event["status"] = status
            event["detail"] = detail
            event["output_summary"] = output_summary
            event["timestamp"] = datetime.now(timezone.utc).isoformat()
            break
    run.timeline_json = json.dumps(timeline, default=str)


def _persist_timeline_records(session: Session, run: Run) -> None:
    timeline = json.loads(run.timeline_json)
    for event in timeline:
        session.add(
            TimelineEventRecord(
                run_id=run.id,
                step_name=event["step"],
                step_status=event["status"],
                duration_ms=int(event.get("duration_ms", 0)),
                short_output=event.get("output_summary", ""),
                detail=event.get("detail", ""),
                created_at=_parse_event_timestamp(event["timestamp"]),
            )
        )


def list_timeline_events_for_run(session: Session, run_id: str) -> List[TimelineEventRecord]:
    statement = (
        select(TimelineEventRecord)
        .where(TimelineEventRecord.run_id == run_id)
        .order_by(TimelineEventRecord.created_at.asc())
    )
    return list(session.exec(statement))


def approve_run(session: Session, run: Run) -> Run:
    run.status = "approved"
    run.approved_at = datetime.now(timezone.utc)
    _update_human_validation_timeline(
        run,
        status="completed",
        detail="Validation humaine effectuee et run approuve.",
        output_summary="Run approuve",
    )
    session.add(run)
    timeline_event = session.exec(
        select(TimelineEventRecord)
        .where(TimelineEventRecord.run_id == run.id)
        .where(TimelineEventRecord.step_name == "reviewed")
    ).first()
    if timeline_event:
        timeline_event.step_status = "completed"
        timeline_event.detail = "Validation humaine effectuee et run approuve."
        timeline_event.short_output = "Run approuve"
        timeline_event.created_at = datetime.now(timezone.utc)
        session.add(timeline_event)
    session.commit()
    session.refresh(run)
    return run


def _build_preference_key(run: Run, payload: FeedbackCreate) -> tuple[str, str]:
    if payload.feedback_type == "category":
        return f"category:{run.category}", run.category
    if payload.feedback_type == "priority":
        return f"priority:{run.category}", run.category
    if payload.feedback_type == "tone":
        return f"tone:{run.category}", run.category
    return f"field:{run.category}:{payload.field_name}", run.category


def save_feedback(session: Session, run: Run, payload: FeedbackCreate) -> Feedback:
    feedback = Feedback(
        run_id=run.id,
        field_name=payload.field_name,
        feedback_type=payload.feedback_type,
        previous_value=payload.previous_value,
        corrected_value=payload.corrected_value,
        comment=payload.comment,
    )
    session.add(feedback)
    run.correction_count += 1
    session.add(run)

    preference_key, preference_scope = _build_preference_key(run, payload)
    existing_preference = session.exec(select(Preference).where(Preference.key == preference_key)).first()
    if existing_preference:
        existing_preference.value = payload.corrected_value
        existing_preference.scope = preference_scope
        existing_preference.updated_at = datetime.now(timezone.utc)
        session.add(existing_preference)
    else:
        session.add(
            Preference(
                key=preference_key,
                value=payload.corrected_value,
                scope=preference_scope,
                source="feedback",
            )
        )

    session.commit()
    session.refresh(feedback)
    return feedback


def list_feedback_for_run(session: Session, run_id: str) -> List[Feedback]:
    statement = select(Feedback).where(Feedback.run_id == run_id).order_by(Feedback.created_at.desc())
    return list(session.exec(statement))


def list_recent_feedback_for_category(session: Session, category: str, limit: int = 5) -> List[FeedbackRead]:
    runs = list(session.exec(select(Run).where(Run.category == category).order_by(Run.created_at.desc())))
    run_ids = {run.id for run in runs}
    if not run_ids:
        return []
    feedback_items = list(session.exec(select(Feedback).order_by(Feedback.created_at.desc())))
    related = [item for item in feedback_items if item.run_id in run_ids][:limit]
    return [to_feedback_read(item, category) for item in related]


def get_preference_hints(session: Session, category: str) -> List[str]:
    statement = select(Preference).where(Preference.scope == category).order_by(Preference.updated_at.desc())
    preferences = list(session.exec(statement))
    return [f"{item.key}={item.value}" for item in preferences]


def get_preference_map(session: Session, category: str) -> Dict[str, str]:
    statement = select(Preference).where(Preference.scope == category).order_by(Preference.updated_at.desc())
    preferences = list(session.exec(statement))
    return {item.key: item.value for item in preferences}


def build_metrics(session: Session) -> MetricsResponse:
    runs = list(session.exec(select(Run)))
    feedback_items = list(session.exec(select(Feedback)))
    timeline_events = list(session.exec(select(TimelineEventRecord)))
    total_runs = len(runs)
    approved = len([run for run in runs if run.status == "approved"])
    approval_rate = round(approved / total_runs, 2) if total_runs else 0.0
    average_score = round(sum(run.automation_score for run in runs) / total_runs, 2) if total_runs else 0.0
    category_distribution = dict(Counter(run.category for run in runs))
    autonomy_mode_distribution = dict(Counter(run.autonomy_mode for run in runs))
    risk_distribution = dict(Counter(run.risk_level for run in runs))
    frequent_feedback = dict(
        Counter(f"{item.feedback_type}:{item.field_name}" for item in feedback_items).most_common(5)
    )

    step_totals: dict[str, list[int]] = defaultdict(list)
    for event in timeline_events:
        step_totals[event.step_name].append(int(event.duration_ms))
    average_step_latency_ms = {
        step: round(sum(values) / len(values), 2)
        for step, values in sorted(step_totals.items())
        if values
    }

    return MetricsResponse(
        total_runs=total_runs,
        approval_rate=approval_rate,
        average_score=average_score,
        category_distribution=category_distribution,
        frequent_feedback=frequent_feedback,
        average_step_latency_ms=average_step_latency_ms,
        autonomy_mode_distribution=autonomy_mode_distribution,
        risk_distribution=risk_distribution,
    )


def to_run_detail(session: Session, run: Run) -> RunDetailResponse:
    recent_category_feedback = list_recent_feedback_for_category(session, run.category)
    timeline_records = list_timeline_events_for_run(session, run.id)
    if timeline_records:
        timeline_payload = [
            {
                "step": event.step_name,
                "status": event.step_status,
                "detail": event.detail,
                "timestamp": event.created_at,
                "duration_ms": event.duration_ms,
                "output_summary": event.short_output,
            }
            for event in timeline_records
        ]
    else:
        timeline_payload = json.loads(run.timeline_json)
    return RunDetailResponse(
        run_id=run.id,
        request_id=run.request_id,
        created_at=run.created_at,
        input_text=run.input_text,
        input_type=run.input_type,
        mode=run.mode,
        requested_mode=run.mode,
        category=run.category,
        confidence=run.confidence,
        rationale=run.rationale,
        extracted_fields=json.loads(run.extracted_fields_json),
        summary=run.summary,
        generated_output=run.generated_output,
        output_type=run.output_type,
        strategy=json.loads(run.strategy_json),
        explainability=json.loads(run.explainability_json),
        timeline=timeline_payload,
        automation_score=run.automation_score,
        score_breakdown=ScoreBreakdown(**json.loads(run.score_breakdown_json)),
        risk_level=run.risk_level,
        autonomy_mode=run.autonomy_mode,
        estimated_time_saved_minutes=run.estimated_time_saved_minutes,
        autonomy_recommendation=run.autonomy_recommendation,
        status=run.status,
        latency_ms=run.latency_ms,
        estimated_cost=run.estimated_cost,
        correction_count=run.correction_count,
        used_preferences=json.loads(run.used_preferences_json),
        recent_category_feedback=recent_category_feedback,
    )


def to_feedback_read(feedback: Feedback, request_category: Optional[str] = None) -> FeedbackRead:
    return FeedbackRead(
        id=feedback.id,
        run_id=feedback.run_id,
        field_name=feedback.field_name,
        feedback_type=feedback.feedback_type,
        previous_value=feedback.previous_value,
        corrected_value=feedback.corrected_value,
        comment=feedback.comment,
        created_at=feedback.created_at,
        request_category=request_category,
    )
