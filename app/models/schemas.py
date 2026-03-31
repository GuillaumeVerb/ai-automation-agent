from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


AutonomyMode = Literal["suggestion_only", "assisted", "low_risk_auto"]
RiskLevel = Literal["low", "medium", "high"]
FeedbackType = Literal["category", "priority", "tone", "extracted_field"]


class TimelineEvent(BaseModel):
    step: str
    status: str
    detail: str
    timestamp: datetime
    duration_ms: int = 0
    output_summary: str = ""


class Explainability(BaseModel):
    category: str
    confidence: float
    signals: List[str]
    strategy: List[str]
    rationale: str
    risk_level: RiskLevel
    diagnostics: List[str] = Field(default_factory=list)
    provider_status: Optional[str] = None


class ExtractedFields(BaseModel):
    priority: str
    subject: str
    deadline: Optional[str] = None
    actor: Optional[str] = None
    action_requested: str
    channel: str
    tone: str


class ScoreResult(BaseModel):
    global_score: int = Field(ge=0, le=100)
    confidence_score: int = Field(ge=0, le=100)
    risk_score: int = Field(ge=0, le=100)
    completeness_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    autonomy_mode: AutonomyMode
    estimated_time_saved_minutes: int
    rationale: str


class RunCreate(BaseModel):
    text: str
    input_type: str = "text"
    mode: AutonomyMode = "assisted"
    preferred_output: Optional[str] = None

    @field_validator("mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: str) -> str:
        aliases = {
            "suggestion": "suggestion_only",
            "suggestion_only": "suggestion_only",
            "assisted": "assisted",
            "auto_low_risk": "low_risk_auto",
            "low_risk_auto": "low_risk_auto",
        }
        normalized = aliases.get(str(value), value)
        if normalized not in {"suggestion_only", "assisted", "low_risk_auto"}:
            raise ValueError("Unsupported mode")
        return normalized


class RunSummaryResponse(BaseModel):
    run_id: str
    category: str
    confidence: float
    summary: str
    strategy: List[str]
    automation_score: int
    risk_level: RiskLevel


class FeedbackCreate(BaseModel):
    field_name: str
    feedback_type: FeedbackType
    corrected_value: str
    previous_value: Optional[str] = None
    comment: Optional[str] = None


class FeedbackRead(BaseModel):
    id: str
    run_id: str
    field_name: str
    feedback_type: FeedbackType
    previous_value: Optional[str]
    corrected_value: str
    comment: Optional[str]
    created_at: datetime
    request_category: Optional[str] = None


class ScoreBreakdown(BaseModel):
    global_score: int
    confidence_score: int
    risk_score: int
    completeness_score: int
    estimated_time_saved_minutes: int
    rationale: str


class RunDetailResponse(BaseModel):
    run_id: str
    request_id: str
    created_at: datetime
    input_text: str
    input_type: str
    mode: AutonomyMode
    requested_mode: AutonomyMode
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
    score_breakdown: ScoreBreakdown
    risk_level: RiskLevel
    autonomy_mode: AutonomyMode
    estimated_time_saved_minutes: int
    autonomy_recommendation: str
    status: str
    latency_ms: int
    estimated_cost: float
    correction_count: int
    used_preferences: List[str]
    recent_category_feedback: List[FeedbackRead] = Field(default_factory=list)


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
    average_step_latency_ms: Dict[str, float]
    autonomy_mode_distribution: Dict[str, int]
    risk_distribution: Dict[str, int]
