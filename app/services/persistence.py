import json
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlmodel import Session, select

from app.models.feedback import Feedback
from app.models.preference import Preference
from app.models.run import Run
from app.models.schemas import FeedbackCreate, FeedbackRead, MetricsResponse, RunDetailResponse


def create_run_record(session: Session, run: Run) -> Run:
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def list_runs(session: Session, limit: int = 50) -> List[Run]:
    statement = select(Run).order_by(Run.created_at.desc()).limit(limit)
    return list(session.exec(statement))


def get_run(session: Session, run_id: str) -> Optional[Run]:
    return session.get(Run, run_id)


def approve_run(session: Session, run: Run) -> Run:
    run.status = "approved"
    run.approved_at = datetime.now(timezone.utc)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def save_feedback(session: Session, run: Run, payload: FeedbackCreate) -> Feedback:
    feedback = Feedback(
        run_id=run.id,
        field_name=payload.field_name,
        previous_value=payload.previous_value,
        corrected_value=payload.corrected_value,
        comment=payload.comment,
    )
    session.add(feedback)
    run.correction_count += 1
    session.add(run)

    preference_key = f"{payload.field_name}:{run.category}"
    existing_preference = session.exec(select(Preference).where(Preference.key == preference_key)).first()
    if existing_preference:
        existing_preference.value = payload.corrected_value
        existing_preference.updated_at = datetime.now(timezone.utc)
        session.add(existing_preference)
    else:
        session.add(Preference(key=preference_key, value=payload.corrected_value, source="feedback"))

    session.commit()
    session.refresh(feedback)
    return feedback


def list_feedback_for_run(session: Session, run_id: str) -> List[Feedback]:
    statement = select(Feedback).where(Feedback.run_id == run_id).order_by(Feedback.created_at.desc())
    return list(session.exec(statement))


def get_preference_hints(session: Session, category: str) -> List[str]:
    statement = select(Preference).where(Preference.key.contains(f":{category}"))
    preferences = list(session.exec(statement))
    return [f"{item.key}={item.value}" for item in preferences]


def build_metrics(session: Session) -> MetricsResponse:
    runs = list(session.exec(select(Run)))
    feedback_items = list(session.exec(select(Feedback)))
    total_runs = len(runs)
    approved = len([run for run in runs if run.status == "approved"])
    approval_rate = round(approved / total_runs, 2) if total_runs else 0.0
    average_score = round(sum(run.automation_score for run in runs) / total_runs, 2) if total_runs else 0.0
    category_distribution = dict(Counter(run.category for run in runs))
    frequent_feedback = dict(Counter(item.field_name for item in feedback_items).most_common(5))
    return MetricsResponse(
        total_runs=total_runs,
        approval_rate=approval_rate,
        average_score=average_score,
        category_distribution=category_distribution,
        frequent_feedback=frequent_feedback,
    )


def to_run_detail(run: Run) -> RunDetailResponse:
    return RunDetailResponse(
        run_id=run.id,
        request_id=run.request_id,
        created_at=run.created_at,
        input_text=run.input_text,
        input_type=run.input_type,
        mode=run.mode,
        category=run.category,
        confidence=run.confidence,
        rationale=run.rationale,
        extracted_fields=json.loads(run.extracted_fields_json),
        summary=run.summary,
        generated_output=run.generated_output,
        output_type=run.output_type,
        strategy=json.loads(run.strategy_json),
        explainability=json.loads(run.explainability_json),
        timeline=json.loads(run.timeline_json),
        automation_score=run.automation_score,
        risk_level=run.risk_level,
        estimated_time_saved_minutes=run.estimated_time_saved_minutes,
        autonomy_recommendation=run.autonomy_recommendation,
        status=run.status,
        latency_ms=run.latency_ms,
        estimated_cost=run.estimated_cost,
        correction_count=run.correction_count,
        used_preferences=json.loads(run.used_preferences_json),
    )


def to_feedback_read(feedback: Feedback) -> FeedbackRead:
    return FeedbackRead(
        id=feedback.id,
        run_id=feedback.run_id,
        field_name=feedback.field_name,
        previous_value=feedback.previous_value,
        corrected_value=feedback.corrected_value,
        comment=feedback.comment,
        created_at=feedback.created_at,
    )
