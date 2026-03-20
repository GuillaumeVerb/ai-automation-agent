from app.models.schemas import ExtractedFields
from app.services.scorer import compute_automation_score


def test_high_confidence_low_priority_can_recommend_low_risk_auto():
    score = compute_automation_score(
        category="reporting",
        confidence=0.94,
        extracted_fields=ExtractedFields(
            priority="low",
            subject="Weekly KPI review",
            deadline="2026-03-21",
            actor="Ops",
            action_requested="prepare_report",
            channel="text",
            tone="neutral",
        ),
        mode="low_risk_auto",
    )
    assert score.global_score >= 80
    assert score.autonomy_mode == "low_risk_auto"


def test_medium_case_recommends_assisted():
    score = compute_automation_score(
        category="support",
        confidence=0.68,
        extracted_fields=ExtractedFields(
            priority="medium",
            subject="Ticket issue",
            deadline=None,
            actor=None,
            action_requested="triage_issue",
            channel="email",
            tone="urgent",
        ),
        mode="assisted",
    )
    assert 55 <= score.global_score < 80
    assert score.autonomy_mode == "assisted"


def test_low_confidence_high_risk_recommends_suggestion_only():
    score = compute_automation_score(
        category="support",
        confidence=0.32,
        extracted_fields=ExtractedFields(
            priority="high",
            subject="Demande sans sujet explicite",
            deadline=None,
            actor=None,
            action_requested="assess_request",
            channel="email",
            tone="urgent",
        ),
        mode="low_risk_auto",
    )
    assert score.global_score < 55
    assert score.autonomy_mode == "suggestion_only"


def test_completeness_score_drops_when_key_fields_are_missing():
    rich = compute_automation_score(
        category="reporting",
        confidence=0.75,
        extracted_fields=ExtractedFields(
            priority="low",
            subject="Quarterly report",
            deadline="2026-03-21",
            actor="Finance",
            action_requested="prepare_report",
            channel="text",
            tone="neutral",
        ),
        mode="assisted",
    )
    sparse = compute_automation_score(
        category="reporting",
        confidence=0.75,
        extracted_fields=ExtractedFields(
            priority="low",
            subject="Demande sans sujet explicite",
            deadline=None,
            actor=None,
            action_requested="assess_request",
            channel="text",
            tone="neutral",
        ),
        mode="assisted",
    )
    assert rich.completeness_score > sparse.completeness_score
