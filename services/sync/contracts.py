"""
Data Contracts and Schema Envelopes for NEXUS Phase 25 Synchronization.
Defines canonical synchronization operations, batch envelopes, results, and audit events.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SyncEntityType(str, Enum):
    INCIDENT = "INCIDENT"
    EVIDENCE = "EVIDENCE"
    RESOURCE_REQUEST = "RESOURCE_REQUEST"
    STATUS_UPDATE = "STATUS_UPDATE"


class SyncOperationType(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class SyncStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"
    RETRYABLE_ERROR = "RETRYABLE_ERROR"


class SyncConflictType(str, Enum):
    STATE_VERSION_CONFLICT = "STATE_VERSION_CONFLICT"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    IDEMPOTENCY_KEY_REUSE = "IDEMPOTENCY_KEY_REUSE"
    UNSAFE_FIELD_MERGE = "UNSAFE_FIELD_MERGE"


class SyncOperation(BaseModel):
    """Canonical client synchronization operation."""
    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(..., min_length=3, description="Client-generated stable operation ID")
    entity_type: SyncEntityType = Field(..., description="Target entity domain category")
    entity_id: str = Field(..., min_length=2, description="Target entity identifier")
    operation_type: SyncOperationType = Field(..., description="Action to perform")
    payload: Dict[str, Any] = Field(..., description="Domain payload conforming to canonical schema")
    schema_version: str = Field(default="1.0.0", description="Contract schema version")
    base_state_version: Optional[int] = Field(None, description="Known Digital Twin state version on client creation")
    client_created_at: str = Field(..., description="Client creation timestamp (ISO-8601)")
    client_id: str = Field(default="FIELD_DEVICE", description="Identifier of originating field officer/device")
    attempt_count: int = Field(default=0, ge=0, description="Number of transmission attempts")


class SyncBatchRequest(BaseModel):
    """Batch of synchronization operations submitted by Field PWA."""
    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., description="Field unit client identifier")
    client_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    operations: List[SyncOperation] = Field(..., min_length=1, max_length=100)


class SyncOperationResult(BaseModel):
    """Per-operation server outcome."""
    operation_id: str
    entity_id: str
    entity_type: SyncEntityType
    status: SyncStatus
    server_state_version: Optional[int] = None
    server_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message: Optional[str] = None
    conflict_type: Optional[SyncConflictType] = None
    server_state: Optional[Dict[str, Any]] = None
    result_data: Optional[Dict[str, Any]] = None


class SyncBatchResponse(BaseModel):
    """Batch synchronization response."""
    batch_id: str
    processed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_operations: int
    accepted_count: int
    duplicate_count: int
    conflict_count: int
    rejected_count: int
    results: List[SyncOperationResult]


class SyncAuditEventType(str, Enum):
    SYNC_STARTED = "SYNC_STARTED"
    OPERATION_RECEIVED = "OPERATION_RECEIVED"
    OPERATION_ACCEPTED = "OPERATION_ACCEPTED"
    OPERATION_DUPLICATE = "OPERATION_DUPLICATE"
    OPERATION_CONFLICT = "OPERATION_CONFLICT"
    OPERATION_REJECTED = "OPERATION_REJECTED"
    OPERATION_FAILED = "OPERATION_FAILED"
    SYNC_COMPLETED = "SYNC_COMPLETED"


class SyncAuditEvent(BaseModel):
    """Immutable audit trail record for synchronization events."""
    event_id: str
    operation_id: str
    event_type: SyncAuditEventType
    entity_type: SyncEntityType
    entity_id: str
    actor_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: SyncStatus
    error_code: Optional[str] = None
    state_version: Optional[int] = None
    details: Optional[str] = None
