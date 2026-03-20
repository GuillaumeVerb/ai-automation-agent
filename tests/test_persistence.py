from sqlmodel import Session

from app.db.session import engine, init_db
from app.models.schemas import FeedbackCreate, RunCreate
from app.services.orchestrator import create_run
from app.services.persistence import build_metrics, list_recent_feedback_for_category, save_feedback


def test_feedback_persistence_stores_type_and_updates_metrics():
    init_db()
    with Session(engine) as session:
        run, _ = create_run(
            session,
            RunCreate(
                text="Please reply to the client and classify this request.",
                input_type="email",
                mode="assisted",
            ),
        )
        feedback = save_feedback(
            session,
            run,
            FeedbackCreate(
                field_name="category",
                feedback_type="category",
                corrected_value="commercial",
                comment="This is a sales conversation",
            ),
        )
        assert feedback.feedback_type == "category"

        recent = list_recent_feedback_for_category(session, run.category)
        assert recent
        assert recent[0].feedback_type == "category"

        metrics = build_metrics(session)
        assert "average_step_latency_ms" in metrics.model_dump()
        assert "autonomy_mode_distribution" in metrics.model_dump()
