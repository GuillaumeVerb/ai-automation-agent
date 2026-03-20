from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Feedback(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"fb_{uuid4().hex}", primary_key=True)
    run_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    field_name: str
    feedback_type: str = "extracted_field"
    previous_value: Optional[str] = None
    corrected_value: str
    comment: Optional[str] = None
