"""
Synchronization REST API Endpoints (Phase 25).
Provides:
- POST /api/v1/sync: Batch synchronization of offline operations.
- GET  /api/v1/sync/events: Chronological audit trail of synchronization events.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from services.recommendations.governance.roles import (
    AuthenticatedActor,
    get_current_actor,
)
from services.sync.contracts import (
    SyncAuditEvent,
    SyncAuditEventType,
    SyncBatchRequest,
    SyncBatchResponse,
)
from services.sync.queue.processor import SyncQueueProcessor

router = APIRouter(prefix="/api/v1/sync", tags=["Synchronization & Idempotency"])

# Shared global sync processor instance
_sync_processor = SyncQueueProcessor()


def get_sync_processor() -> SyncQueueProcessor:
    return _sync_processor


@router.post("", response_model=SyncBatchResponse, status_code=status.HTTP_200_OK)
def synchronize_operations(
    batch: SyncBatchRequest,
    actor: AuthenticatedActor = Depends(get_current_actor),
    processor: SyncQueueProcessor = Depends(get_sync_processor),
) -> SyncBatchResponse:
    """
    Synchronize a batch of offline field operations with the central authority.
    Processes idempotently, detects payload alteration key reuse, validates
    optimistic concurrency, and records append-only audit events.
    """
    return processor.process_batch(batch, actor)


@router.get("/events", response_model=List[SyncAuditEvent])
def list_sync_audit_events(
    operation_id: Optional[str] = Query(None, description="Filter by operation ID"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    event_type: Optional[SyncAuditEventType] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    actor: AuthenticatedActor = Depends(get_current_actor),
    processor: SyncQueueProcessor = Depends(get_sync_processor),
) -> List[SyncAuditEvent]:
    """
    Query chronological synchronization audit events.
    """
    return processor.event_ledger.list_events(
        operation_id=operation_id,
        entity_id=entity_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
