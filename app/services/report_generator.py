from app.models.schemas import ExtractedFields
from app.services.llm_engine import complete_text
from app.services.prompt_loader import load_prompt


def generate_report(text: str, extracted_fields: ExtractedFields, category: str, request_id: str = "") -> str:
    llm_report = complete_text(
        load_prompt("report"),
        f"Request:\n{text}\n\nStructured fields:\n{extracted_fields.model_dump_json()}",
        request_id=request_id,
        task_name="report",
    )
    if llm_report:
        return llm_report.strip()

    deadline = extracted_fields.deadline or "Non precisee"
    actor = extracted_fields.actor or "Non identifie"
    excerpt = text[:220].strip()

    if category == "reporting":
        return (
            "# Executive Summary\n\n"
            "## Scope\n"
            f"- Sujet: {extracted_fields.subject}\n"
            f"- Deadline: {deadline}\n"
            f"- Owner pressenti: {actor}\n\n"
            "## Key Reading\n"
            f"- Demande principale: {extracted_fields.action_requested}\n"
            f"- Niveau de priorite: {extracted_fields.priority}\n"
            f"- Ton du demandeur: {extracted_fields.tone}\n\n"
            "## Recommended Output\n"
            "- Structurer les indicateurs ou le reporting attendu\n"
            "- Mettre en avant les anomalies, tendances ou blocages\n"
            "- Valider les destinataires et le format final avant diffusion\n\n"
            "## Source Excerpt\n"
            f"{excerpt}"
        )

    if category == "support":
        return (
            "# Incident Brief\n\n"
            "## Situation\n"
            f"- Sujet: {extracted_fields.subject}\n"
            f"- Priorite: {extracted_fields.priority}\n"
            f"- Deadline ou attente: {deadline}\n"
            f"- Reporter: {actor}\n\n"
            "## Triage Notes\n"
            f"- Action demandee: {extracted_fields.action_requested}\n"
            "- Verifier la reproductibilite et le perimetre d'impact\n"
            "- Confirmer les signaux techniques disponibles\n\n"
            "## Recommended Next Steps\n"
            "- Ouvrir ou enrichir le ticket de suivi\n"
            "- Prioriser selon l'impact operationnel\n"
            "- Partager un retour d'avancement a l'emetteur\n\n"
            "## Source Excerpt\n"
            f"{excerpt}"
        )

    if category == "commercial":
        return (
            "# Account Action Brief\n\n"
            "## Opportunity Context\n"
            f"- Sujet: {extracted_fields.subject}\n"
            f"- Contact ou owner: {actor}\n"
            f"- Priorite: {extracted_fields.priority}\n\n"
            "## What The Client Seems To Need\n"
            f"- Intention detectee: {extracted_fields.action_requested}\n"
            f"- Deadline: {deadline}\n"
            f"- Ton: {extracted_fields.tone}\n\n"
            "## Recommended Sales Actions\n"
            "- Clarifier le besoin et le niveau d'urgence\n"
            "- Preparer une reponse structuree ou un next step commercial\n"
            "- Confirmer le bon owner avant envoi\n\n"
            "## Source Excerpt\n"
            f"{excerpt}"
        )

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
        f"- Resume source: {excerpt}\n\n"
        "## Actions recommandees\n"
        "- Valider le traitement humain.\n"
        "- Prioriser si la demande bloque une operation critique.\n"
        "- Journaliser la decision finale."
    )
