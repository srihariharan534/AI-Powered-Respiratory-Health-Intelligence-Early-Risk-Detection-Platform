"""
Unit & End-to-End Tests for Phase 25 (Synchronization, Idempotency, and Conflict Resolution).
Validates:
1. Canonical sync batch processing and schema validation.
2. At-least-once delivery: duplicate submission returns cached outcome without duplicate domain mutation.
3. Payload tampering: same operation_id with different payload raises IDEMPOTENCY_KEY_REUSE conflict.
4. Optimistic concurrency: state version mismatch triggers STATE_VERSION_CONFLICT.
5. RBAC authorization enforcement on sync endpoints.
6. Partial success batch processing: independent operation isolation.
7. Append-only sync audit ledger completeness.
8. REST API endpoints (/api/v1/sync and /api/v1/sync/events).
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.repositories.incident_service import IncidentService
from services.api.app.routes.sync import router as sync_router
from services.recommendations.governance.roles import AuthenticatedActor, UserRole
from services.sync.conflict_resolution.engine import ConflictResolutionEngine
from services.sync.contracts import (
    SyncAuditEventType,
    SyncBatchRequest,
    SyncConflictType,
    SyncEntityType,
    SyncOperation,
    SyncOperationType,
    SyncStatus,
)
from services.sync.event_log.ledger import SyncEventLedger
from services.sync.idempotency.store import (
    IdempotencyKeyReuseError,
    IdempotencyStore,
    compute_payload_hash,
)
from services.sync.queue.processor import SyncQueueProcessor
from services.sync.retry.backoff import RetryPolicy


@pytest.fixture
def clean_sync_env():
    """Provides isolated DigitalTwin, IncidentService, IdempotencyStore, and Processor."""
    dt = DigitalTwinStateManager(initial_version=10)
    incident_service = IncidentService(digital_twin=dt)
    idempotency_store = IdempotencyStore()
    event_ledger = SyncEventLedger()
    conflict_engine = ConflictResolutionEngine()

    processor = SyncQueueProcessor(
        incident_service=incident_service,
        digital_twin=dt,
        idempotency_store=idempotency_store,
        event_ledger=event_ledger,
        conflict_engine=conflict_engine,
    )

    actor = AuthenticatedActor(actor_id="FIELD_OFFICER_01", role=UserRole.FIELD_OFFICER)

    return {
        "dt": dt,
        "incident_service": incident_service,
        "idempotency_store": idempotency_store,
        "event_ledger": event_ledger,
        "conflict_engine": conflict_engine,
        "processor": processor,
        "actor": actor,
    }


def test_payload_hash_deterministic():
    payload_a = {"incident_id": "INC-001", "severity": "HIGH", "priority": 1}
    payload_b = {"priority": 1, "severity": "HIGH", "incident_id": "INC-001"}
    assert compute_payload_hash(payload_a) == compute_payload_hash(payload_b)


def test_single_incident_create_sync(clean_sync_env):
    processor = clean_sync_env["processor"]
    actor = clean_sync_env["actor"]

    incident_payload = {
        "schema_version": "1.0.0",
        "incident_id": "INC-SYNC-001",
        "event_type": "FLOOD_INUNDATION",
        "severity": "HIGH",
        "status": "OPEN",
        "priority": 1,
        "location": {"type": "Point", "coordinates": [80.2230, 13.0180]},
        "reported_at": "2026-09-20T08:00:00Z",
        "reported_by": "FIELD_OFFICER_01",
        "description": "Severe inundation near culvert 4",
        "source": "field_officer",
    }

    op = SyncOperation(
        operation_id="OP-001",
        entity_type=SyncEntityType.INCIDENT,
        entity_id="INC-SYNC-001",
        operation_type=SyncOperationType.CREATE,
        payload=incident_payload,
        schema_version="1.0.0",
        base_state_version=10,
        client_created_at="2026-09-20T08:00:00Z",
    )

    batch = SyncBatchRequest(client_id="FIELD_OFFICER_01", operations=[op])
    response = processor.process_batch(batch, actor)

    assert response.total_operations == 1
    assert response.accepted_count == 1
    assert response.duplicate_count == 0
    assert response.results[0].status == SyncStatus.ACCEPTED
    assert response.results[0].entity_id == "INC-SYNC-001"

    # Verify incident exists in authoritative incident service
    created = clean_sync_env["incident_service"].get_incident("INC-SYNC-001")
    assert created["incident_id"] == "INC-SYNC-001"


def test_idempotent_duplicate_submission(clean_sync_env):
    processor = clean_sync_env["processor"]
    actor = clean_sync_env["actor"]

    incident_payload = {
        "schema_version": "1.0.0",
        "incident_id": "INC-SYNC-002",
        "event_type": "FLOOD_INUNDATION",
        "severity": "CRITICAL",
        "status": "OPEN",
        "priority": 1,
        "location": {"type": "Point", "coordinates": [80.2230, 13.0180]},
        "reported_at": "2026-09-20T08:00:00Z",
        "reported_by": "FIELD_OFFICER_01",
        "description": "Embankment rupture",
        "source": "field_officer",
    }

    op = SyncOperation(
        operation_id="OP-DUPLICATE-001",
        entity_type=SyncEntityType.INCIDENT,
        entity_id="INC-SYNC-002",
        operation_type=SyncOperationType.CREATE,
        payload=incident_payload,
        client_created_at="2026-09-20T08:00:00Z",
    )

    batch1 = SyncBatchRequest(client_id="FIELD_OFFICER_01", operations=[op])
    res1 = processor.process_batch(batch1, actor)
    assert res1.accepted_count == 1

    # Second submission with same operation_id and same payload (simulate network retry)
    batch2 = SyncBatchRequest(client_id="FIELD_OFFICER_01", operations=[op])
    res2 = processor.process_batch(batch2, actor)

    assert res2.accepted_count == 0
    assert res2.duplicate_count == 1
    assert res2.results[0].status == SyncStatus.DUPLICATE
    assert res2.results[0].operation_id == "OP-DUPLICATE-001"


def test_idempotency_key_reuse_payload_altered(clean_sync_env):
    processor = clean_sync_env["processor"]
    actor = clean_sync_env["actor"]

    payload1 = {
        "schema_version": "1.0.0",
        "incident_id": "INC-SYNC-003",
        "event_type": "FLOOD_INUNDATION",
        "severity": "LOW",
        "status": "OPEN",
        "priority": 3,
        "location": {"type": "Point", "coordinates": [80.2230, 13.0180]},
        "reported_at": "2026-09-20T08:00:00Z",
        "reported_by": "FIELD_OFFICER_01",
        "description": "Puddle overflow",
        "source": "field_officer",
    }

    op1 = SyncOperation(
        operation_id="OP-ALTERED-001",
        entity_type=SyncEntityType.INCIDENT,
        entity_id="INC-SYNC-003",
        operation_type=SyncOperationType.CREATE,
        payload=payload1,
        client_created_at="2026-09-20T08:00:00Z",
    )
    processor.process_batch(SyncBatchRequest(client_id="FIELD_OFFICER_01", operations=[op1]), actor)

    # Same operation_id but altered payload
    payload2 = {**payload1, "severity": "CRITICAL"}
    op2 = SyncOperation(
        operation_id="OP-ALTERED-001",
        entity_type=SyncEntityType.INCIDENT,
        entity_id="INC-SYNC-003",
        operation_type=SyncOperationType.CREATE,
        payload=payload2,
        client_created_at="2026-09-20T08:00:00Z",
    )
    res2 = processor.process_batch(SyncBatchRequest(client_id="FIELD_OFFICER_01", operations=[op2]), actor)

    assert res2.conflict_count == 1
    assert res2.results[0].status == SyncStatus.CONFLICT
    assert res2.results[0].conflict_type == SyncConflictType.IDEMPOTENCY_KEY_REUSE


def test_state_version_conflict(clean_sync_env):
    processor = clean_sync_env["processor"]
    actor = clean_sync_env["actor"]
    dt = clean_sync_env["dt"]

    # First, create incident
    payload = {
        "schema_version": "1.0.0",
        "incident_id": "INC-SYNC-004",
        "event_type": "FLOOD_INUNDATION",
        "severity": "LOW",
        "status": "OPEN",
        "priority": 2,
        "location": {"type": "Point", "coordinates": [80.2230, 13.0180]},
        "reported_at": "2026-09-20T08:00:00Z",
        "reported_by": "FIELD_OFFICER_01",
        "description": "Initial report",
        "source": "field_officer",
    }
    op_create = SyncOperation(
        operation_id="OP-CREATE-004",
        entity_type=SyncEntityType.INCIDENT,
        entity_id="INC-SYNC-004",
        operation_type=SyncOperationType.CREATE,
        payload=payload,
        client_created_at="2026-09-20T08:00:00Z",
    )
    processor.process_batch(SyncBatchRequest(client_id="FIELD_OFFICER_01", operations=[op_create]), actor)

    # Now advance Digital Twin state version manually
    dt._version = 20

    # Client submits update based on stale version 10
    op_update = SyncOperation(
        operation_id="OP-UPDATE-004",
        entity_type=SyncEntityType.INCIDENT,
        entity_id="INC-SYNC-004",
        operation_type=SyncOperationType.UPDATE,
        payload={"severity": "HIGH"},
        base_state_version=10,
        client_created_at="2026-09-20T08:05:00Z",
    )
    res_update = processor.process_batch(SyncBatchRequest(client_id="FIELD_OFFICER_01", operations=[op_update]), actor)

    assert res_update.conflict_count == 1
    assert res_update.results[0].status == SyncStatus.CONFLICT
    assert res_update.results[0].conflict_type == SyncConflictType.STATE_VERSION_CONFLICT
    assert res_update.results[0].server_state["server_current_version"] == 20


def test_rbac_unauthorized_role_rejected(clean_sync_env):
    processor = clean_sync_env["processor"]
    viewer_actor = AuthenticatedActor(actor_id="VIEWER_01", role=UserRole.VIEWER)

    op = SyncOperation(
        operation_id="OP-UNAUTH-001",
        entity_type=SyncEntityType.INCIDENT,
        entity_id="INC-UNAUTH-001",
        operation_type=SyncOperationType.CREATE,
        payload={"dummy": "payload"},
        client_created_at="2026-09-20T08:00:00Z",
    )
    batch = SyncBatchRequest(client_id="VIEWER_01", operations=[op])
    res = processor.process_batch(batch, viewer_actor)

    assert res.rejected_count == 1
    assert res.results[0].status == SyncStatus.REJECTED
    assert "not authorized" in res.results[0].message.lower()


def test_batch_partial_success_isolation(clean_sync_env):
    processor = clean_sync_env["processor"]
    actor = clean_sync_env["actor"]

    # Valid incident 1
    valid_payload = {
        "schema_version": "1.0.0",
        "incident_id": "INC-VALID-001",
        "event_type": "FLOOD_INUNDATION",
        "severity": "MEDIUM",
        "status": "OPEN",
        "priority": 2,
        "location": {"type": "Point", "coordinates": [80.2230, 13.0180]},
        "reported_at": "2026-09-20T08:00:00Z",
        "reported_by": "FIELD_OFFICER_01",
        "description": "Standing water",
        "source": "field_officer",
    }
    op1 = SyncOperation(
        operation_id="OP-BATCH-1",
        entity_type=SyncEntityType.INCIDENT,
        entity_id="INC-VALID-001",
        operation_type=SyncOperationType.CREATE,
        payload=valid_payload,
        client_created_at="2026-09-20T08:00:00Z",
    )

    # Invalid operation (unsupported schema version)
    op2 = SyncOperation(
        operation_id="OP-BATCH-2",
        entity_type=SyncEntityType.INCIDENT,
        entity_id="INC-INVALID-002",
        operation_type=SyncOperationType.CREATE,
        payload=valid_payload,
        schema_version="9.9.9",
        client_created_at="2026-09-20T08:00:00Z",
    )

    # Valid resource request
    op3 = SyncOperation(
        operation_id="OP-BATCH-3",
        entity_type=SyncEntityType.RESOURCE_REQUEST,
        entity_id="REQ-BATCH-001",
        operation_type=SyncOperationType.CREATE,
        payload={"resource_type": "RESCUE_BOAT", "quantity": 2},
        client_created_at="2026-09-20T08:00:00Z",
    )

    batch = SyncBatchRequest(client_id="FIELD_OFFICER_01", operations=[op1, op2, op3])
    res = processor.process_batch(batch, actor)

    assert res.total_operations == 3
    assert res.accepted_count == 2
    assert res.rejected_count == 1
    assert res.results[0].status == SyncStatus.ACCEPTED
    assert res.results[1].status == SyncStatus.REJECTED
    assert res.results[2].status == SyncStatus.ACCEPTED


def test_sync_audit_event_ledger(clean_sync_env):
    processor = clean_sync_env["processor"]
    actor = clean_sync_env["actor"]
    event_ledger = clean_sync_env["event_ledger"]

    op = SyncOperation(
        operation_id="OP-AUDIT-001",
        entity_type=SyncEntityType.RESOURCE_REQUEST,
        entity_id="REQ-AUDIT-001",
        operation_type=SyncOperationType.CREATE,
        payload={"resource_type": "MEDICAL_KIT", "quantity": 5},
        client_created_at="2026-09-20T08:00:00Z",
    )
    processor.process_batch(SyncBatchRequest(client_id="FIELD_OFFICER_01", operations=[op]), actor)

    events = event_ledger.list_events(operation_id="OP-AUDIT-001")
    assert len(events) >= 1
    assert events[0].operation_id == "OP-AUDIT-001"
    assert events[0].event_type == SyncAuditEventType.OPERATION_ACCEPTED
    assert events[0].actor_id == "FIELD_OFFICER_01"


def test_retry_policy_logic():
    policy = RetryPolicy(base_delay_ms=1000, max_delay_ms=10000, max_attempts=5, jitter_ms=0)
    assert policy.is_retryable(503) is True
    assert policy.is_retryable(429) is True
    assert policy.is_retryable(400) is False
    assert policy.is_retryable(403) is False

    assert policy.compute_delay_ms(0) == 1000
    assert policy.compute_delay_ms(1) == 2000
    assert policy.compute_delay_ms(2) == 4000
    assert policy.compute_delay_ms(4) == 10000  # Capped at max_delay
    assert policy.has_exceeded_max_attempts(5) is True


def test_sync_rest_api():
    app = FastAPI()
    app.include_router(sync_router)
    client = TestClient(app)

    batch_payload = {
        "client_id": "FIELD_OFFICER_01",
        "client_timestamp": "2026-09-20T08:00:00Z",
        "operations": [
            {
                "operation_id": "OP-REST-001",
                "entity_type": "RESOURCE_REQUEST",
                "entity_id": "REQ-REST-001",
                "operation_type": "CREATE",
                "payload": {"resource_type": "FOOD_WATER", "quantity": 10},
                "schema_version": "1.0.0",
                "client_created_at": "2026-09-20T08:00:00Z",
                "client_id": "FIELD_OFFICER_01",
                "attempt_count": 0,
            }
        ],
    }

    # Post batch with auth headers
    headers = {"X-Actor-Id": "FIELD_OFFICER_01", "X-Actor-Role": "FIELD_OFFICER"}
    resp = client.post("/api/v1/sync", json=batch_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted_count"] == 1
    assert data["results"][0]["status"] == "ACCEPTED"

    # Query events endpoint
    events_resp = client.get("/api/v1/sync/events", headers=headers)
    assert events_resp.status_code == 200
    events_data = events_resp.json()
    assert len(events_data) >= 1
