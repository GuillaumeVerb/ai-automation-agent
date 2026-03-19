from app.models.schemas import ScoreResult
from app.services.llm_engine import complete_json


def compute_automation_score(category: str, confidence: float, priority: str, mode: str) -> ScoreResult:
    llm_payload = complete_json(
        "Assess automation readiness. Return JSON with automation_score, risk_level, estimated_time_saved_minutes, "
        "autonomy_recommendation, rationale.",
        f"Category={category}\nConfidence={confidence}\nPriority={priority}\nMode={mode}",
    )
    if llm_payload:
        return ScoreResult(
            automation_score=int(llm_payload.get("automation_score", 50)),
            risk_level=str(llm_payload.get("risk_level", "medium")),
            estimated_time_saved_minutes=int(llm_payload.get("estimated_time_saved_minutes", 10)),
            autonomy_recommendation=str(llm_payload.get("autonomy_recommendation", "human_review")),
            rationale=str(llm_payload.get("rationale", "Score fourni par le provider configure.")),
        )
    base = int(confidence * 100)
    if category == "support":
        base -= 10
    if priority == "high":
        base -= 20
    elif priority == "medium":
        base -= 8
    if mode == "suggestion":
        base = min(base + 5, 100)

    score = max(15, min(base, 95))
    if score >= 75:
        risk = "low"
        autonomy = "ready_for_assisted"
        saved = 20
    elif score >= 50:
        risk = "medium"
        autonomy = "human_review"
        saved = 12
    else:
        risk = "high"
        autonomy = "manual_only"
        saved = 5

    return ScoreResult(
        automation_score=score,
        risk_level=risk,
        estimated_time_saved_minutes=saved,
        autonomy_recommendation=autonomy,
        rationale=f"Score calcule a partir de la confiance, de la categorie {category}, de la priorite {priority} et du mode {mode}.",
    )
