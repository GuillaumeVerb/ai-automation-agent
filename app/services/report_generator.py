from app.models.schemas import ExtractedFields
from app.services.llm_engine import complete_text
from app.services.prompt_loader import load_prompt


def generate_report(text: str, extracted_fields: ExtractedFields, request_id: str = "") -> str:
    llm_report = complete_text(
        load_prompt("report"),
        f"Request:\n{text}\n\nStructured fields:\n{extracted_fields.model_dump_json()}",
        request_id=request_id,
    )
    if llm_report:
        return llm_report.strip()
    deadline = extracted_fields.deadline or "Non precisee"
    actor = extracted_fields.actor or "Non identifie"
    return (
        "# Mini Report\n\n"
        "## Contexte\n"
        f"- Sujet: {extracted_fields.subject}\n"
        f"- Acteur: {actor}\n"
        f"- Priorite: {extracted_fields.priority}\n"
        f"- Deadline: {deadline}\n\n"
        "## Points cles\n"
        f"- Action demandee: {extracted_fields.action_requested}\n"
        f"- Ton detecte: {extracted_fields.tone}\n"
        f"- Resume source: {text[:160].strip()}\n\n"
        "## Actions recommandees\n"
        "- Valider le traitement humain.\n"
        "- Prioriser si la demande bloque une operation critique.\n"
        "- Journaliser la decision finale."
    )
