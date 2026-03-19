from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Run(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"run_{uuid4().hex}", primary_key=True)
    request_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    input_text: str
    input_type: str
    mode: str = "assisted"
    category: str
    confidence: float
    rationale: str
    extracted_fields_json: str
    summary: str
    generated_output: str
    output_type: str
    strategy_json: str
    explainability_json: str
    timeline_json: str
    automation_score: int
    risk_level: str
    estimated_time_saved_minutes: int = 0
    autonomy_recommendation: str = "human_review"
    status: str = "pending_review"
    latency_ms: int = 0
    estimated_cost: float = 0.0
    used_preferences_json: str = "[]"
    correction_count: int = 0
    approved_at: Optional[datetime] = None
