from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Field, SQLModel


class TimelineEventRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"te_{uuid4().hex}", primary_key=True)
    run_id: str = Field(index=True)
    step_name: str = Field(index=True)
    step_status: str
    duration_ms: int = 0
    short_output: str = ""
    detail: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
