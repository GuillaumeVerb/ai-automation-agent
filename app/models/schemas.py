from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    step: str
    status: str
    detail: str
    timestamp: datetime


class Explainability(BaseModel):
    category: str
    confidence: float
    signals: List[str]
    strategy: List[str]
    rationale: str


class ExtractedFields(BaseModel):
    priority: str
    subject: str
    deadline: Optional[str] = None
    actor: Optional[str] = None
    action_requested: str
    channel: str
    tone: str


class ScoreResult(BaseModel):
    automation_score: int = Field(ge=0, le=100)
    risk_level: str
    estimated_time_saved_minutes: int
    autonomy_recommendation: str
    rationale: str


class RunCreate(BaseModel):
    text: str
    input_type: str = "text"
    mode: str = "assisted"
    preferred_output: Optional[str] = None


class RunSummaryResponse(BaseModel):
    run_id: str
    category: str
    confidence: float
    summary: str
    strategy: List[str]
    automation_score: int
    risk_level: str


class RunDetailResponse(BaseModel):
    run_id: str
    request_id: str
    created_at: datetime
    input_text: str
    input_type: str
    mode: str
    category: str
    confidence: float
    rationale: str
    extracted_fields: Dict[str, Any]
    summary: str
    generated_output: str
    output_type: str
    strategy: List[str]
    explainability: Explainability
    timeline: List[TimelineEvent]
    automation_score: int
    risk_level: str
    estimated_time_saved_minutes: int
    autonomy_recommendation: str
    status: str
    latency_ms: int
    estimated_cost: float
    correction_count: int
    used_preferences: List[str]


class FeedbackCreate(BaseModel):
    field_name: str
    corrected_value: str
    previous_value: Optional[str] = None
    comment: Optional[str] = None


class FeedbackRead(BaseModel):
    id: str
    run_id: str
    field_name: str
    previous_value: Optional[str]
    corrected_value: str
    comment: Optional[str]
    created_at: datetime


class ApprovalResponse(BaseModel):
    run_id: str
    status: str


class RegenerateRequest(BaseModel):
    strategy_hint: Optional[str] = None
    preferred_output: Optional[str] = None


class MetricsResponse(BaseModel):
    total_runs: int
    approval_rate: float
    average_score: float
    category_distribution: Dict[str, int]
    frequent_feedback: Dict[str, int]
