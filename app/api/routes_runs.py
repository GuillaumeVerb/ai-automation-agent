import json
import time
from typing import Iterator, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session as SQLModelSession
from sqlmodel import Session

from app.db.session import engine, get_session
from app.models.schemas import ApprovalResponse, FeedbackCreate, FeedbackRead, RegenerateRequest, RunCreate, RunDetailResponse, RunSummaryResponse
from app.services.orchestrator import initialize_run, process_run_async
from app.services.persistence import (
    approve_run,
    get_run,
    list_feedback_for_run,
    list_runs,
    list_timeline_events_for_run,
    save_feedback,
    to_feedback_read,
    to_run_detail,
)


router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


def _sse_message(data: dict[str, object]) -> str:
    return f"data: {json.dumps(data, default=str)}\n\n"


def _run_snapshot_payload(run) -> dict[str, object]:
    return {
        "type": "run_snapshot",
        "run_id": run.id,
        "run_status": run.status,
        "category": run.category,
        "confidence": run.confidence,
        "summary": run.summary,
        "generated_output": run.generated_output,
        "output_type": run.output_type,
        "automation_score": run.automation_score,
        "risk_level": run.risk_level,
        "autonomy_mode": run.autonomy_mode,
        "estimated_time_saved_minutes": run.estimated_time_saved_minutes,
        "strategy": json.loads(run.strategy_json),
        "extracted_fields": json.loads(run.extracted_fields_json),
        "used_preferences": json.loads(run.used_preferences_json),
    }


def _stream_run_events(run_id: str) -> Iterator[str]:
    emitted_event_ids: set[str] = set()
    last_snapshot_signature = ""
    terminal_statuses = {"pending_review", "approved", "failed"}

    while True:
        with SQLModelSession(engine) as session:
            run = get_run(session, run_id)
            if not run:
                yield _sse_message({"type": "error", "run_id": run_id, "message": "Run not found"})
                return

            timeline_events = list_timeline_events_for_run(session, run_id)
            for event in timeline_events:
                if event.id in emitted_event_ids:
                    continue
                emitted_event_ids.add(event.id)
                yield _sse_message(
                    {
                        "type": "timeline_event",
                        "run_id": run_id,
                        "run_status": run.status,
                        "step": event.step_name,
                        "status": event.step_status,
                        "detail": event.detail,
                        "duration_ms": event.duration_ms,
                        "output_summary": event.short_output,
                        "timestamp": event.created_at.isoformat(),
                    }
                )

            snapshot = _run_snapshot_payload(run)
            snapshot_signature = json.dumps(snapshot, sort_keys=True)
            if snapshot_signature != last_snapshot_signature:
                last_snapshot_signature = snapshot_signature
                yield _sse_message(snapshot)

            if run.status in terminal_statuses:
                yield _sse_message({"type": "run_status", "run_id": run_id, "run_status": run.status})
                return

        time.sleep(0.12)


@router.post("", response_model=RunSummaryResponse, status_code=status.HTTP_202_ACCEPTED)
def create_run_endpoint(
    payload: RunCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> RunSummaryResponse:
    run, response = initialize_run(session, payload)
    background_tasks.add_task(process_run_async, run.id, payload.model_dump())
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


@router.get("/{run_id}/stream")
def stream_run_endpoint(run_id: str, session: Session = Depends(get_session)) -> StreamingResponse:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return StreamingResponse(_stream_run_events(run_id), media_type="text/event-stream")


@router.post("/{run_id}/approve", response_model=ApprovalResponse)
def approve_run_endpoint(run_id: str, session: Session = Depends(get_session)) -> ApprovalResponse:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "pending_review":
        raise HTTPException(status_code=409, detail="Run not ready for approval")
    run = approve_run(session, run)
    return ApprovalResponse(run_id=run.id, status=run.status)


@router.post("/{run_id}/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def feedback_run_endpoint(run_id: str, payload: FeedbackCreate, session: Session = Depends(get_session)) -> FeedbackRead:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status == "processing":
        raise HTTPException(status_code=409, detail="Run still processing")
    feedback = save_feedback(session, run, payload)
    return to_feedback_read(feedback)


@router.post("/{run_id}/regenerate", response_model=RunSummaryResponse, status_code=status.HTTP_202_ACCEPTED)
def regenerate_run_endpoint(
    run_id: str,
    payload: RegenerateRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> RunSummaryResponse:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status == "processing":
        raise HTTPException(status_code=409, detail="Run still processing")
    requested_output = payload.preferred_output
    if not requested_output and payload.strategy_hint:
        if "email" in payload.strategy_hint.lower():
            requested_output = "email_reply"
        elif "report" in payload.strategy_hint.lower():
            requested_output = "report"
    regenerated_payload = RunCreate(
        text=run.input_text,
        input_type=run.input_type,
        mode=run.mode,
        preferred_output=requested_output,
    )
    new_run, response = initialize_run(session, regenerated_payload)
    background_tasks.add_task(process_run_async, new_run.id, regenerated_payload.model_dump())
    return response


@router.get("/{run_id}/feedback", response_model=List[FeedbackRead])
def list_feedback_endpoint(run_id: str, session: Session = Depends(get_session)) -> List[FeedbackRead]:
    run = get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return [to_feedback_read(item) for item in list_feedback_for_run(session, run_id)]
