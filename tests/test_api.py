from fastapi.testclient import TestClient

from app.main import app


def test_create_get_feedback_and_metrics_flow():
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/runs",
            json={
                "text": "Bonjour, notre export KPI plante depuis hier. Merci de preparer aussi une reponse client.",
                "input_type": "email",
                "mode": "assisted",
            },
        )
        assert create_response.status_code == 201
        created = create_response.json()

        detail_response = client.get(f"/api/v1/runs/{created['run_id']}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["category"] in {"support", "reporting", "commercial", "administratif", "autre"}
        assert detail["requested_mode"] == "assisted"
        assert detail["autonomy_mode"] in {"suggestion_only", "assisted", "low_risk_auto"}
        assert "timeline" in detail
        assert "score_breakdown" in detail
        assert "recent_category_feedback" in detail

        feedback_response = client.post(
            f"/api/v1/runs/{created['run_id']}/feedback",
            json={
                "field_name": "tone",
                "feedback_type": "tone",
                "corrected_value": "polite",
                "comment": "Prefer a softer reply tone",
            },
        )
        assert feedback_response.status_code == 201
        feedback = feedback_response.json()
        assert feedback["feedback_type"] == "tone"

        regenerate_response = client.post(
            f"/api/v1/runs/{created['run_id']}/regenerate",
            json={"preferred_output": "report", "strategy_hint": "report"},
        )
        assert regenerate_response.status_code == 201
        regenerated = regenerate_response.json()
        assert regenerated["run_id"] != created["run_id"]
        assert "generate_report" in regenerated["strategy"]

        approve_response = client.post(f"/api/v1/runs/{created['run_id']}/approve")
        assert approve_response.status_code == 200

        approved_detail = client.get(f"/api/v1/runs/{created['run_id']}").json()
        review_step = next(event for event in approved_detail["timeline"] if event["step"] == "reviewed")
        assert review_step["status"] == "completed"

        metrics_response = client.get("/api/v1/metrics")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert metrics["total_runs"] >= 1
        assert "average_step_latency_ms" in metrics
        assert "autonomy_mode_distribution" in metrics
