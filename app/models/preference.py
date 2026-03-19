from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Preference(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"pref_{uuid4().hex}", primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
    source: str = "feedback"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
