from app.services.extractor import extract_fields


def test_extractor_returns_expected_json_shape():
    result = extract_fields("Urgent: please prepare a report on KPI trends before 2026-03-21.")
    payload = result.model_dump()
    assert payload["priority"] == "high"
    assert payload["deadline"] == "2026-03-21"
    assert payload["action_requested"] in {"prepare_report", "prepare_reply", "triage_issue", "assess_request"}
