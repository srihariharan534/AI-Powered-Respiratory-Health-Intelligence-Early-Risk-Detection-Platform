"""
Decision Replay Timeline and Event History Engine (Phase 30 & Feature A).
Allows replaying the exact chronological operational decision loop.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DecisionReplayEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stage: str
    headline: str
    entity_id: Optional[str] = None
    data_snapshot: Dict[str, Any] = Field(default_factory=dict)
    state_version: int
    actor: str = "SYSTEM"


class DecisionReplayEngine:
    """
    Maintains a deterministic chronological sequence of all major operational events
    allowing complete audit replay.
    """

    def __init__(self) -> None:
        self._events: List[DecisionReplayEvent] = []

    def record(
        self,
        stage: str,
        headline: str,
        entity_id: Optional[str] = None,
        data_snapshot: Optional[Dict[str, Any]] = None,
        state_version: int = 1,
        actor: str = "SYSTEM",
    ) -> DecisionReplayEvent:
        evt = DecisionReplayEvent(
            stage=stage,
            headline=headline,
            entity_id=entity_id,
            data_snapshot=data_snapshot or {},
            state_version=state_version,
            actor=actor,
        )
        self._events.append(evt)
        return evt

    def get_timeline(self) -> List[DecisionReplayEvent]:
        return list(self._events)
