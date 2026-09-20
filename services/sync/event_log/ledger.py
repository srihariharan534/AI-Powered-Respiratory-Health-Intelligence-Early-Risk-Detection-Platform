"""
Append-Only Sync Event Log (Phase 25).
Maintains immutable chronological event stream for all incoming synchronization operations.
"""

import threading
from datetime import datetime, timezone
from typing import List, Optional

from services.sync.contracts import (
    SyncAuditEvent,
    SyncAuditEventType,
    SyncEntityType,
    SyncStatus,
)


class SyncEventLedger:
    """
    Thread-safe, append-only synchronization audit ledger.
    No updates or deletions allowed.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: List[SyncAuditEvent] = []

    def record_event(
        self,
        operation_id: str,
        event_type: SyncAuditEventType,
        entity_type: SyncEntityType,
        entity_id: str,
        actor_id: str,
        status: SyncStatus,
        error_code: Optional[str] = None,
        state_version: Optional[int] = None,
        details: Optional[str] = None,
    ) -> SyncAuditEvent:
        """Appends a new audit event to the ledger."""
        event_id = f"SYNC-EVT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        event = SyncAuditEvent(
            event_id=event_id,
            operation_id=operation_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            status=status,
            error_code=error_code,
            state_version=state_version,
            details=details,
        )
        with self._lock:
            self._events.append(event)
            return event

    def list_events(
        self,
        operation_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        event_type: Optional[SyncAuditEventType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SyncAuditEvent]:
        """Queries events in chronological order with optional filtering."""
        with self._lock:
            filtered = self._events
            if operation_id:
                filtered = [e for e in filtered if e.operation_id == operation_id]
            if entity_id:
                filtered = [e for e in filtered if e.entity_id == entity_id]
            if event_type:
                filtered = [e for e in filtered if e.event_type == event_type]

            return [e.model_copy() for e in filtered[offset : offset + limit]]

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        """Testing utility to clear event ledger."""
        with self._lock:
            self._events.clear()
