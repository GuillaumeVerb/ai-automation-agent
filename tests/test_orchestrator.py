import json

from sqlmodel import Session

from app.db.session import engine, init_db
from app.models.schemas import FeedbackCreate, RunCreate
from app.services.orchestrator import create_run
from app.services.persistence import get_preference_hints, save_feedback


def test_orchestrator_creates_v2_run_with_enriched_payload():
    init_db()
    with Session(engine) as session:
        run, response = create_run(
            session,
            RunCreate(
                text="Please build a KPI report for the weekly operations review.",
                input_type="text",
                mode="assisted",
            ),
        )
    assert run.id.startswith("run_")
    assert response.run_id == run.id
    assert response.category in {"reporting", "autre"}
    assert response.automation_score >= 0


def test_orchestrator_attaches_timeline_and_score_breakdown():
    init_db()
    with Session(engine) as session:
        run, _ = create_run(
            session,
            RunCreate(
                text="Urgent: please prepare a report for tomorrow and share a reply draft.",
                input_type="text",
                mode="low_risk_auto",
            ),
        )
        detail_steps = [event["step"] for event in json.loads(run.timeline_json)]
        assert detail_steps == [
            "input_received",
            "preprocessed",
            "classified",
            "extracted",
            "generated",
            "scored",
            "reviewed",
            "saved",
        ]
        score_breakdown = json.loads(run.score_breakdown_json)
        assert "global_score" in score_breakdown
        assert "confidence_score" in score_breakdown
        assert "completeness_score" in score_breakdown
        explainability = json.loads(run.explainability_json)
        assert "diagnostics" in explainability
        assert "heuristic_fallback_active" in explainability["diagnostics"]
        assert explainability["provider_status"] == "heuristic_fallback_active"


def test_feedback_preferences_are_reused_as_hints():
    init_db()
    with Session(engine) as session:
        run, _ = create_run(
            session,
            RunCreate(
                text="Please prepare a customer reply for a KPI issue.",
                input_type="email",
                mode="assisted",
            ),
        )
        save_feedback(
            session,
            run,
            FeedbackCreate(
                field_name="tone",
                feedback_type="tone",
                corrected_value="polite",
                comment="Keep a softer wording",
            ),
        )
        hints = get_preference_hints(session, run.category)
        assert any("tone:" in hint for hint in hints)
