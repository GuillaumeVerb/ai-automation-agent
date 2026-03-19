import re
from uuid import uuid4


def preprocess_text(raw_text: str) -> tuple[str, str]:
    cleaned = re.sub(r"\s+", " ", raw_text.strip())
    request_id = f"req_{uuid4().hex}"
    return cleaned, request_id
