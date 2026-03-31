from typing import List, Optional

from app.models.schemas import Explainability


def build_explainability(
    category: str,
    confidence: float,
    signals: list[str],
    strategy: list[str],
    classifier_rationale: str,
    risk_level: str,
    requested_mode: str,
    recommended_mode: str,
    diagnostics: Optional[List[str]] = None,
    provider_status: Optional[str] = None,
) -> Explainability:
    rationale_parts = [classifier_rationale]
    if recommended_mode != requested_mode:
        rationale_parts.append(
            f"Mode demande '{requested_mode}' ajuste vers une recommandation '{recommended_mode}' selon le score d'automatisation."
        )
    if diagnostics:
        rationale_parts.append(f"Etat runtime: {', '.join(diagnostics)}.")
    rationale_parts.append(f"Risque estime: {risk_level}.")
    rationale = " ".join(part.strip() for part in rationale_parts if part).strip()
    return Explainability(
        category=category,
        confidence=confidence,
        signals=signals or ["general_request"],
        strategy=strategy,
        rationale=rationale,
        risk_level=risk_level,
        diagnostics=diagnostics or [],
        provider_status=provider_status,
    )
