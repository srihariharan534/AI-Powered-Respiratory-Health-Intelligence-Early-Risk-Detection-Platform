"""
Append-Only Audit Ledger Repository (Phase 21).
Maintains immutable chronological event stream for recommendation governance.
Direct deletion or mutation of events is strictly disallowed.
"""

import threading
from typing import List, Optional
from services.recommendations.contracts import (
    AuditEventType,
    RecommendationAuditEvent,
    RecommendationDecisionRecord,
)


class AuditLedger:
    """
    Thread-safe, append-only audit ledger storing governance events and durable decision records.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: List[RecommendationAuditEvent] = []
        self._decision_records: List[RecommendationDecisionRecord] = []
        self._idempotency_map: dict[str, RecommendationDecisionRecord] = {}

    def append_event(self, event: RecommendationAuditEvent) -> RecommendationAuditEvent:
        """Appends an event to the immutable ledger."""
        with self._lock:
            # Store a deep copy/validated instance to guarantee immutability
            event_copy = event.model_copy(deep=True)
            self._events.append(event_copy)
            return event_copy

    def save_decision_record(
        self,
        record: RecommendationDecisionRecord,
    ) -> RecommendationDecisionRecord:
        """Stores durable decision record, indexing by idempotency key if provided."""
        with self._lock:
            record_copy = record.model_copy(deep=True)
            self._decision_records.append(record_copy)
            if record.idempotency_key:
                self._idempotency_map[record.idempotency_key] = record_copy
            return record_copy

    def get_decision_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Optional[RecommendationDecisionRecord]:
        """Retrieves cached decision record by idempotency key."""
        with self._lock:
            return self._idempotency_map.get(idempotency_key)

    def list_events(
        self,
        recommendation_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RecommendationAuditEvent]:
        """
        Queries chronological audit events with filtering and pagination.
        Ordered latest first.
        """
        with self._lock:
            filtered = self._events

            if recommendation_id:
                filtered = [e for e in filtered if e.recommendation_id == recommendation_id]
            if event_type:
                filtered = [e for e in filtered if e.event_type == event_type]
            if actor_id:
                filtered = [e for e in filtered if e.actor_id == actor_id]

            # Chronological reverse sort (newest first)
            sorted_events = sorted(filtered, key=lambda e: e.timestamp, reverse=True)
            return [e.model_copy(deep=True) for e in sorted_events[offset : offset + limit]]

    def count_events(
        self,
        recommendation_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
    ) -> int:
        """Counts total matching audit events."""
        with self._lock:
            filtered = self._events
            if recommendation_id:
                filtered = [e for e in filtered if e.recommendation_id == recommendation_id]
            if event_type:
                filtered = [e for e in filtered if e.event_type == event_type]
            return len(filtered)
