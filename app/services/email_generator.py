from app.models.schemas import ExtractedFields
from app.services.llm_engine import complete_text


def generate_email_reply(text: str, extracted_fields: ExtractedFields, style: str = "professional") -> str:
    llm_reply = complete_text(
        "Write a concise professional email reply in French. Keep it clear, reassuring, and action-oriented.",
        f"Request:\n{text}\n\nStructured fields:\n{extracted_fields.model_dump_json()}",
    )
    if llm_reply:
        return llm_reply.strip()
    deadline = extracted_fields.deadline or "des que possible"
    return (
        "Bonjour,\n\n"
        f"Nous avons bien pris en compte votre demande concernant '{extracted_fields.subject}'. "
        f"Le sujet est actuellement qualifie en priorite {extracted_fields.priority}.\n\n"
        f"Nous revenons vers vous avec une mise a jour avant {deadline}. "
        "Si vous avez des elements complementaires, vous pouvez nous les partager en reponse a cet email.\n\n"
        "Bien cordialement,\n"
        "AI Automation Agent"
    )
