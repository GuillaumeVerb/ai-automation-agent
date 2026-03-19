from app.services.classifier import classify_request


def test_classifier_returns_closed_category():
    category, confidence, rationale, signals = classify_request("The dashboard KPI report is broken and urgent.")
    assert category in {"support", "reporting", "commercial", "administratif", "autre"}
    assert confidence > 0
    assert rationale
    assert signals
