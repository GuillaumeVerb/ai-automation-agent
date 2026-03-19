from typing import Dict, List

from app.services.llm_engine import complete_json


CATEGORY_RULES: Dict[str, List[str]] = {
    "support": ["bug", "incident", "erreur", "plante", "probleme", "issue", "helpdesk", "ticket"],
    "reporting": ["report", "kpi", "dashboard", "reporting", "metrics", "weekly", "mensuel", "rapport"],
    "commercial": ["pricing", "quote", "proposal", "vente", "devis", "renewal", "client", "demo"],
    "administratif": ["invoice", "facture", "contrat", "rh", "conge", "admin", "compliance"],
}


def classify_request(text: str) -> tuple[str, float, str, List[str]]:
    llm_payload = complete_json(
        "Classify the request into support, reporting, commercial, administratif, or autre. "
        "Return JSON with keys category, confidence, rationale, and signals.",
        text,
    )
    if llm_payload:
        category = str(llm_payload.get("category", "autre"))
        if category not in {"support", "reporting", "commercial", "administratif", "autre"}:
            category = "autre"
        confidence = float(llm_payload.get("confidence", 0.5))
        rationale = str(llm_payload.get("rationale", "Classification fournie par le provider configure."))
        signals = llm_payload.get("signals", ["llm_inference"])
        if not isinstance(signals, list) or not signals:
            signals = ["llm_inference"]
        return category, round(max(0.0, min(confidence, 0.99)), 2), rationale, [str(item) for item in signals[:6]]

    lowered = text.lower()
    scores: Dict[str, int] = {category: 0 for category in CATEGORY_RULES}
    matched_signals: Dict[str, List[str]] = {category: [] for category in CATEGORY_RULES}
    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in lowered:
                scores[category] += 1
                matched_signals[category].append(keyword)

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    if best_score == 0:
        return "autre", 0.4, "Aucun signal fort detecte, la demande reste non classee.", ["general_request"]

    confidence = min(0.55 + best_score * 0.12, 0.97)
    rationale = f"Classement '{best_category}' base sur les indices detectes: {', '.join(matched_signals[best_category][:4])}."
    return best_category, round(confidence, 2), rationale, matched_signals[best_category]
