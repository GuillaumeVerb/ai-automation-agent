from sqlmodel import Session

from app.db.session import engine, init_db
from app.models.schemas import RunCreate
from app.services.orchestrator import create_run


def test_orchestrator_creates_reporting_run():
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
