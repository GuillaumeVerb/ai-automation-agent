from app.services.llm_engine import complete_text


def summarize_request(text: str) -> str:
    llm_summary = complete_text("Summarize the request in 2 to 4 concise lines.", text)
    if llm_summary:
        return llm_summary.strip()
    cleaned = text.strip()
    if len(cleaned) <= 180:
        return cleaned
    return f"{cleaned[:177].rstrip()}..."
