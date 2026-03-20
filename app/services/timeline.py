import time
from datetime import datetime, timezone
from typing import List

from app.models.schemas import TimelineEvent


class TimelineTracker:
    def __init__(self) -> None:
        self.events: List[TimelineEvent] = []

    def add_step(self, step: str, detail: str, output_summary: str, started_at: float, status: str = "completed") -> None:
        duration_ms = max(0, int((time.perf_counter() - started_at) * 1000))
        self.events.append(
            TimelineEvent(
                step=step,
                status=status,
                detail=detail,
                timestamp=datetime.now(timezone.utc),
                duration_ms=duration_ms,
                output_summary=output_summary,
            )
        )

    def add_instant(self, step: str, detail: str, output_summary: str, status: str = "completed") -> None:
        self.events.append(
            TimelineEvent(
                step=step,
                status=status,
                detail=detail,
                timestamp=datetime.now(timezone.utc),
                duration_ms=0,
                output_summary=output_summary,
            )
        )
