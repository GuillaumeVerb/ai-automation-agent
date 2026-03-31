from app.models.schemas import ExtractedFields
from app.services.llm_engine import complete_text
from app.services.prompt_loader import load_prompt


def generate_email_reply(
    text: str,
    extracted_fields: ExtractedFields,
    category: str,
    style: str = "professional",
    request_id: str = "",
) -> str:
    del style
    llm_reply = complete_text(
        load_prompt("email_reply"),
        f"Request:\n{text}\n\nStructured fields:\n{extracted_fields.model_dump_json()}",
        request_id=request_id,
        task_name="email_reply",
    )
    if llm_reply:
        return llm_reply.strip()

    deadline = extracted_fields.deadline or "des que possible"
    actor = extracted_fields.actor or "notre equipe"

    if category == "support":
        return (
            "Bonjour,\n\n"
            f"Nous avons bien recu votre signalement concernant '{extracted_fields.subject}'. "
            f"Le dossier est pris en charge avec une priorite {extracted_fields.priority}.\n\n"
            "Prochaines etapes:\n"
            "- qualification technique du probleme\n"
            "- verification de l'impact pour les utilisateurs concernes\n"
            f"- retour de situation avant {deadline}\n\n"
            "Si vous disposez d'un message d'erreur, d'une capture ou d'un horodatage precis, "
            "vous pouvez nous les partager pour accelerer l'analyse.\n\n"
            "Cordialement,\nAI Automation Agent"
        )

    if category == "commercial":
        return (
            "Bonjour,\n\n"
            f"Merci pour votre message au sujet de '{extracted_fields.subject}'. "
            "Nous preparons une reponse structuree afin de revenir vers vous avec les bons elements.\n\n"
            "Prochaines etapes:\n"
            f"- qualification de votre besoin avec {actor}\n"
            "- verification du contexte commercial et des attentes\n"
            f"- retour propose avant {deadline}\n\n"
            "Si vous souhaitez, nous pouvons egalement vous proposer un prochain point pour avancer rapidement.\n\n"
            "Bien cordialement,\nAI Automation Agent"
        )

    if category == "administratif":
        return (
            "Bonjour,\n\n"
            f"Votre demande concernant '{extracted_fields.subject}' a bien ete prise en compte. "
            f"Elle est actuellement en cours de verification avec une priorite {extracted_fields.priority}.\n\n"
            f"Nous reviendrons vers vous avant {deadline} avec une confirmation du traitement ou les points restants.\n\n"
            "Si un document complementaire est necessaire, nous vous le signalerons dans le meme fil.\n\n"
            "Cordialement,\nAI Automation Agent"
        )

    opener = "Merci pour votre message." if extracted_fields.tone == "polite" else "Nous avons bien pris en compte votre demande."
    return (
        "Bonjour,\n\n"
        f"{opener} "
        f"Le sujet '{extracted_fields.subject}' est actuellement analyse avec une priorite {extracted_fields.priority}.\n\n"
        f"Nous reviendrons vers vous avant {deadline} avec la suite recommandee.\n\n"
        "Bien cordialement,\nAI Automation Agent"
    )
