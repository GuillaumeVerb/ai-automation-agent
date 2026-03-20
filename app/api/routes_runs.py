from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.session import get_session
from app.models.schemas import ApprovalResponse, FeedbackCreate, FeedbackRead, RegenerateRequest, RunCreate, RunDetailResponse, RunSummaryResponse
from app.services.orchestrator import create_run, regenerate_run
from app.services.persistence import approve_run, get_run, list_feedback_for_run, list_runs, save_feedback, to_feedback_read, to_run_detail


router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.post("", response_model=RunSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_run_endpoint(payload: RunCreate, session: Session = Depends(get_session)) -> RunSummaryResponse:
    _, response = create_run(session, payload)
    return response


@router.get("", response_model=List[RunDetailResponse])
def list_runs_endpoint(session: Session = Depends(get_session)) -> List[RunDetailResponse]:
    return [to_run_detail(session, run) for run in list_runs(session)]


@router.get("/{run_id}", response_model=RunDetailResponse)
def get_run_endpoint(run_id: str, session: Session = Depends(get_session)) -> RunDetailResponse:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return to_run_detail(session, run)


@router.post("/{run_id}/approve", response_model=ApprovalResponse)
def approve_run_endpoint(run_id: str, session: Session = Depends(get_session)) -> ApprovalResponse:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run = approve_run(session, run)
    return ApprovalResponse(run_id=run.id, status=run.status)


@router.post("/{run_id}/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def feedback_run_endpoint(run_id: str, payload: FeedbackCreate, session: Session = Depends(get_session)) -> FeedbackRead:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    feedback = save_feedback(session, run, payload)
    return to_feedback_read(feedback)


@router.post("/{run_id}/regenerate", response_model=RunSummaryResponse, status_code=status.HTTP_201_CREATED)
def regenerate_run_endpoint(run_id: str, payload: RegenerateRequest, session: Session = Depends(get_session)) -> RunSummaryResponse:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    _, response = regenerate_run(
        session,
        run,
        strategy_hint=payload.strategy_hint,
        preferred_output=payload.preferred_output,
    )
    return response


@router.get("/{run_id}/feedback", response_model=List[FeedbackRead])
def list_feedback_endpoint(run_id: str, session: Session = Depends(get_session)) -> List[FeedbackRead]:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return [to_feedback_read(item) for item in list_feedback_for_run(session, run_id)]
