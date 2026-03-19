from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.models.schemas import MetricsResponse
from app.services.persistence import build_metrics


router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("", response_model=MetricsResponse)
def get_metrics(session: Session = Depends(get_session)) -> MetricsResponse:
    return build_metrics(session)
