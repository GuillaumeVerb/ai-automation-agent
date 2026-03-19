from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_get_feedback_and_metrics_flow():
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
    assert "timeline" in detail

    feedback_response = client.post(
        f"/api/v1/runs/{created['run_id']}/feedback",
        json={"field_name": "summary", "corrected_value": "Correction de resume", "comment": "Raccourcir"},
    )
    assert feedback_response.status_code == 201

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

    metrics_response = client.get("/api/v1/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["total_runs"] >= 1
    assert "support" in metrics["category_distribution"] or metrics["category_distribution"]
