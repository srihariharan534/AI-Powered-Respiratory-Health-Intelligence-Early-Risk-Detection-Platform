"""
Server-side Idempotency Registry (Phase 25).
Protects against at-least-once duplicate delivery and detects payload alteration key reuse.
"""

import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from services.sync.contracts import SyncOperationResult, SyncStatus


def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash of canonical JSON string."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class IdempotencyRecord(BaseModel):
    operation_id: str
    request_hash: str
    entity_type: str
    entity_id: str
    operation_type: str
    status: SyncStatus
    cached_result: SyncOperationResult
    processed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    state_version: Optional[int] = None


class IdempotencyKeyReuseError(Exception):
    """Raised when an operation_id is reused with a different request payload."""
    def __init__(self, operation_id: str, existing_hash: str, incoming_hash: str):
        super().__init__(
            f"IDEMPOTENCY_KEY_REUSE: Operation '{operation_id}' was previously submitted "
            f"with payload hash {existing_hash[:8]}..., but received new hash {incoming_hash[:8]}..."
        )
        self.operation_id = operation_id
        self.existing_hash = existing_hash
        self.incoming_hash = incoming_hash


class IdempotencyStore:
    """
    Thread-safe registry preserving processed operation idempotency records.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, IdempotencyRecord] = {}

    def get_record(self, operation_id: str) -> Optional[IdempotencyRecord]:
        with self._lock:
            return self._store.get(operation_id)

    def check_and_register(
        self,
        operation_id: str,
        payload: Dict[str, Any],
    ) -> Optional[IdempotencyRecord]:
        """
        Checks if operation_id has already been processed:
        - If not seen: returns None (caller proceeds to process).
        - If seen with SAME payload hash: returns existing IdempotencyRecord.
        - If seen with DIFFERENT payload hash: raises IdempotencyKeyReuseError.
        """
        incoming_hash = compute_payload_hash(payload)
        with self._lock:
            existing = self._store.get(operation_id)
            if not existing:
                return None

            if existing.request_hash != incoming_hash:
                raise IdempotencyKeyReuseError(
                    operation_id=operation_id,
                    existing_hash=existing.request_hash,
                    incoming_hash=incoming_hash,
                )

            return existing

    def save_record(
        self,
        operation_id: str,
        payload: Dict[str, Any],
        entity_type: str,
        entity_id: str,
        operation_type: str,
        status: SyncStatus,
        result: SyncOperationResult,
        state_version: Optional[int] = None,
    ) -> IdempotencyRecord:
        """Saves processed operation outcome for future idempotent retries."""
        req_hash = compute_payload_hash(payload)
        record = IdempotencyRecord(
            operation_id=operation_id,
            request_hash=req_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type=operation_type,
            status=status,
            cached_result=result,
            state_version=state_version,
        )
        with self._lock:
            self._store[operation_id] = record
            return record

    def clear(self) -> None:
        """Clears all idempotency records (testing utility)."""
        with self._lock:
            self._store.clear()
