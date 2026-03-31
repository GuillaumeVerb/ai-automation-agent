from app.models.schemas import ExtractedFields
from app.services.email_generator import generate_email_reply
from app.services.report_generator import generate_report


def test_support_email_reply_mentions_incident_steps():
    output = generate_email_reply(
        text="Our dashboard is broken for several users.",
        extracted_fields=ExtractedFields(
            priority="high",
            subject="Dashboard outage",
            deadline="2026-04-02",
            actor="Alice Martin",
            action_requested="prepare_reply",
            channel="email",
            tone="urgent",
        ),
        category="support",
    )
    assert "Prochaines etapes" in output
    assert "Dashboard outage" in output
    assert "2026-04-02" in output


def test_reporting_report_uses_executive_summary_template():
    output = generate_report(
        text="Please prepare the weekly KPI review with anomalies for operations leadership.",
        extracted_fields=ExtractedFields(
            priority="medium",
            subject="Weekly KPI review",
            deadline="2026-04-05",
            actor="Operations",
            action_requested="prepare_report",
            channel="text",
            tone="neutral",
        ),
        category="reporting",
    )
    assert "# Executive Summary" in output
    assert "Recommended Output" in output
    assert "Weekly KPI review" in output
