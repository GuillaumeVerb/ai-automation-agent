from app.models.schemas import ExtractedFields, ScoreResult


def _compute_confidence_score(confidence: float) -> int:
    return max(0, min(int(round(confidence * 100)), 100))


def _compute_risk_score(category: str, priority: str, mode: str) -> tuple[int, str]:
    score = 90
    if category == "support":
        score -= 10
    elif category == "administratif":
        score -= 5

    if priority == "high":
        score -= 35
    elif priority == "medium":
        score -= 15

    if mode == "low_risk_auto":
        score -= 10
    elif mode == "assisted":
        score -= 3

    score = max(5, min(score, 100))
    if score >= 75:
        return score, "low"
    if score >= 45:
        return score, "medium"
    return score, "high"


def _compute_completeness_score(extracted_fields: ExtractedFields) -> int:
    score = 55
    if extracted_fields.subject and extracted_fields.subject != "Demande sans sujet explicite":
        score += 20
    if extracted_fields.action_requested and extracted_fields.action_requested != "assess_request":
        score += 10
    if extracted_fields.deadline:
        score += 5
    if extracted_fields.actor:
        score += 5
    if extracted_fields.tone in {"urgent", "polite", "neutral"}:
        score += 5
    return max(0, min(score, 100))


def _estimate_time_saved(global_score: int) -> int:
    if global_score >= 80:
        return 22
    if global_score >= 55:
        return 12
    return 6


def compute_automation_score(
    category: str,
    confidence: float,
    extracted_fields: ExtractedFields,
    mode: str,
    request_id: str = "",
) -> ScoreResult:
    del request_id
    confidence_score = _compute_confidence_score(confidence)
    risk_score, risk_level = _compute_risk_score(category, extracted_fields.priority, mode)
    completeness_score = _compute_completeness_score(extracted_fields)
    global_score = int(round(confidence_score * 0.45 + risk_score * 0.35 + completeness_score * 0.20))
    global_score = max(0, min(global_score, 100))

    if global_score >= 80 and risk_level == "low":
        autonomy_mode = "low_risk_auto"
    elif global_score >= 55:
        autonomy_mode = "assisted"
    else:
        autonomy_mode = "suggestion_only"

    estimated_time_saved_minutes = _estimate_time_saved(global_score)
    rationale = (
        f"Score global {global_score}/100 calcule via confiance={confidence_score}, "
        f"risque={risk_score} et completude={completeness_score} pour une demande {category} "
        f"en priorite {extracted_fields.priority} sous mode {mode}."
    )

    return ScoreResult(
        global_score=global_score,
        confidence_score=confidence_score,
        risk_score=risk_score,
        completeness_score=completeness_score,
        risk_level=risk_level,
        autonomy_mode=autonomy_mode,
        estimated_time_saved_minutes=estimated_time_saved_minutes,
        rationale=rationale,
    )
