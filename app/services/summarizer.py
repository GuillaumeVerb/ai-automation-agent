from app.services.llm_engine import complete_text
from app.services.prompt_loader import load_prompt


def summarize_request(text: str, request_id: str = "") -> str:
    llm_summary = complete_text(load_prompt("summary"), text, request_id=request_id, task_name="summary")
    if llm_summary:
        return llm_summary.strip()
    cleaned = text.strip()
    if len(cleaned) <= 180:
        return cleaned
    return f"{cleaned[:177].rstrip()}..."
