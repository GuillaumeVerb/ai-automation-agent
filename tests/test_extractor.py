from app.services.extractor import extract_fields


def test_extractor_returns_expected_json_shape():
    result = extract_fields("Urgent: please prepare a report on KPI trends before 2026-03-21.")
    payload = result.model_dump()
    assert payload["priority"] == "high"
    assert payload["deadline"] == "2026-03-21"
    assert payload["action_requested"] in {"prepare_report", "prepare_reply", "triage_issue", "assess_request"}


def test_extractor_uses_email_subject_and_sender_lines():
    result = extract_fields(
        "From: Alice Martin <alice@example.com>\n"
        "Subject: Q2 KPI review for finance\n\n"
        "Please prepare a report before 04/04/2026."
    )
    payload = result.model_dump()
    assert payload["actor"] == "Alice Martin"
    assert payload["subject"] == "Q2 KPI review for finance"
    assert payload["channel"] == "email"
    assert payload["deadline"] == "2026-04-04"


def test_extractor_detects_json_channel():
    result = extract_fields('{"type":"report_request","priority":"medium"}')
    assert result.channel == "json"
