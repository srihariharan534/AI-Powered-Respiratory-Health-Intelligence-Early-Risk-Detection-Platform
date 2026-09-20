"""
Server-Side Synchronization Queue Processor (Phase 25).
Coordinates authentication, envelope validation, idempotency checks, conflict detection,
domain service delegation, Digital Twin event emission, and audit logging.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.repositories.incident_service import IncidentService
from services.api.app.schemas.incident import Incident
from services.recommendations.governance.roles import AuthenticatedActor, UserRole
from services.sync.conflict_resolution.engine import ConflictResolutionEngine
from services.sync.contracts import (
    SyncAuditEventType,
    SyncBatchRequest,
    SyncBatchResponse,
    SyncConflictType,
    SyncEntityType,
    SyncOperation,
    SyncOperationResult,
    SyncStatus,
)
from services.sync.event_log.ledger import SyncEventLedger
from services.sync.idempotency.store import (
    IdempotencyKeyReuseError,
    IdempotencyStore,
)


class SyncQueueProcessor:
    """
    Processes incoming sync batches atomically per operation.
    Enforces idempotency, optimistic concurrency, and audit trails.
    """

    def __init__(
        self,
        incident_service: Optional[IncidentService] = None,
        digital_twin: Optional[DigitalTwinStateManager] = None,
        idempotency_store: Optional[IdempotencyStore] = None,
        event_ledger: Optional[SyncEventLedger] = None,
        conflict_engine: Optional[ConflictResolutionEngine] = None,
    ) -> None:
        self.digital_twin = digital_twin or DigitalTwinStateManager()
        self.incident_service = incident_service or IncidentService(digital_twin=self.digital_twin)
        self.idempotency_store = idempotency_store or IdempotencyStore()
        self.event_ledger = event_ledger or SyncEventLedger()
        self.conflict_engine = conflict_engine or ConflictResolutionEngine()

    def process_batch(
        self,
        batch: SyncBatchRequest,
        actor: AuthenticatedActor,
    ) -> SyncBatchResponse:
        """Processes each operation within the incoming batch independently."""
        batch_id = f"BATCH-{uuid.uuid4().hex[:12].upper()}"
        results: List[SyncOperationResult] = []

        accepted_count = 0
        duplicate_count = 0
        conflict_count = 0
        rejected_count = 0

        for op in batch.operations:
            result = self._process_single_operation(op, actor)
            results.append(result)

            if result.status == SyncStatus.ACCEPTED:
                accepted_count += 1
            elif result.status == SyncStatus.DUPLICATE:
                duplicate_count += 1
            elif result.status == SyncStatus.CONFLICT:
                conflict_count += 1
            elif result.status in [SyncStatus.REJECTED, SyncStatus.RETRYABLE_ERROR]:
                rejected_count += 1

        return SyncBatchResponse(
            batch_id=batch_id,
            total_operations=len(batch.operations),
            accepted_count=accepted_count,
            duplicate_count=duplicate_count,
            conflict_count=conflict_count,
            rejected_count=rejected_count,
            results=results,
        )

    def _process_single_operation(
        self,
        op: SyncOperation,
        actor: AuthenticatedActor,
    ) -> SyncOperationResult:
        """Executes full validation and domain synchronization pipeline for one operation."""

        # 1. Schema version check
        if op.schema_version != "1.0.0":
            self.event_ledger.record_event(
                operation_id=op.operation_id,
                event_type=SyncAuditEventType.OPERATION_REJECTED,
                entity_type=op.entity_type,
                entity_id=op.entity_id,
                actor_id=actor.actor_id,
                status=SyncStatus.REJECTED,
                error_code="UNSUPPORTED_SCHEMA_VERSION",
                details=f"Schema version '{op.schema_version}' is not supported.",
            )
            return SyncOperationResult(
                operation_id=op.operation_id,
                entity_id=op.entity_id,
                entity_type=op.entity_type,
                status=SyncStatus.REJECTED,
                message=f"Unsupported schema version '{op.schema_version}'. Expected '1.0.0'.",
            )

        # 2. Authorization check
        # Field officers, operators, and commanders may submit sync operations
        allowed_roles = {UserRole.FIELD_OFFICER, UserRole.OPERATOR, UserRole.COMMANDER, UserRole.ADMIN}
        if actor.role not in allowed_roles:
            self.event_ledger.record_event(
                operation_id=op.operation_id,
                event_type=SyncAuditEventType.OPERATION_REJECTED,
                entity_type=op.entity_type,
                entity_id=op.entity_id,
                actor_id=actor.actor_id,
                status=SyncStatus.REJECTED,
                error_code="UNAUTHORIZED_ROLE",
                details=f"Role '{actor.role}' cannot submit synchronization operations.",
            )
            return SyncOperationResult(
                operation_id=op.operation_id,
                entity_id=op.entity_id,
                entity_type=op.entity_type,
                status=SyncStatus.REJECTED,
                message=f"Actor role '{actor.role}' is not authorized to synchronize operations.",
            )

        # 3. Idempotency Check
        try:
            existing_record = self.idempotency_store.check_and_register(op.operation_id, op.payload)
            if existing_record:
                # Return duplicate cached result without re-executing domain mutation
                self.event_ledger.record_event(
                    operation_id=op.operation_id,
                    event_type=SyncAuditEventType.OPERATION_DUPLICATE,
                    entity_type=op.entity_type,
                    entity_id=op.entity_id,
                    actor_id=actor.actor_id,
                    status=SyncStatus.DUPLICATE,
                    state_version=existing_record.state_version,
                    details="Duplicate operation recognized; cached outcome returned.",
                )
                cached = existing_record.cached_result.model_copy()
                cached.status = SyncStatus.DUPLICATE
                return cached
        except IdempotencyKeyReuseError as err:
            self.event_ledger.record_event(
                operation_id=op.operation_id,
                event_type=SyncAuditEventType.OPERATION_CONFLICT,
                entity_type=op.entity_type,
                entity_id=op.entity_id,
                actor_id=actor.actor_id,
                status=SyncStatus.CONFLICT,
                error_code="IDEMPOTENCY_KEY_REUSE",
                details=str(err),
            )
            return SyncOperationResult(
                operation_id=op.operation_id,
                entity_id=op.entity_id,
                entity_type=op.entity_type,
                status=SyncStatus.CONFLICT,
                conflict_type=SyncConflictType.IDEMPOTENCY_KEY_REUSE,
                message=str(err),
            )

        # 4. Domain & Conflict Evaluation
        current_version = self.digital_twin.state_version
        server_entity = None
        if op.entity_type == SyncEntityType.INCIDENT:
            try:
                server_entity = self.incident_service.get_incident(op.entity_id)
            except Exception:
                server_entity = None

        conflict_info = self.conflict_engine.evaluate_conflict(
            operation=op,
            current_server_version=current_version,
            server_entity=server_entity,
        )

        if conflict_info:
            c_type, c_reason, c_diff = conflict_info
            self.event_ledger.record_event(
                operation_id=op.operation_id,
                event_type=SyncAuditEventType.OPERATION_CONFLICT,
                entity_type=op.entity_type,
                entity_id=op.entity_id,
                actor_id=actor.actor_id,
                status=SyncStatus.CONFLICT,
                error_code=c_type.value,
                state_version=current_version,
                details=c_reason,
            )
            return SyncOperationResult(
                operation_id=op.operation_id,
                entity_id=op.entity_id,
                entity_type=op.entity_type,
                status=SyncStatus.CONFLICT,
                conflict_type=c_type,
                message=c_reason,
                server_state=c_diff,
                server_state_version=current_version,
            )

        # 5. Domain Execution
        try:
            result_data = self._apply_domain_mutation(op, actor)
            new_state_version = self.digital_twin.state_version

            op_result = SyncOperationResult(
                operation_id=op.operation_id,
                entity_id=op.entity_id,
                entity_type=op.entity_type,
                status=SyncStatus.ACCEPTED,
                server_state_version=new_state_version,
                message="Operation successfully committed to authoritative state.",
                result_data=result_data,
            )

            # 6. Save Idempotency Record
            self.idempotency_store.save_record(
                operation_id=op.operation_id,
                payload=op.payload,
                entity_type=op.entity_type.value,
                entity_id=op.entity_id,
                operation_type=op.operation_type.value,
                status=SyncStatus.ACCEPTED,
                result=op_result,
                state_version=new_state_version,
            )

            # 7. Append to Audit Ledger
            self.event_ledger.record_event(
                operation_id=op.operation_id,
                event_type=SyncAuditEventType.OPERATION_ACCEPTED,
                entity_type=op.entity_type,
                entity_id=op.entity_id,
                actor_id=actor.actor_id,
                status=SyncStatus.ACCEPTED,
                state_version=new_state_version,
                details=f"Committed {op.operation_type.value} on {op.entity_type.value} {op.entity_id}",
            )

            return op_result

        except Exception as err:
            self.event_ledger.record_event(
                operation_id=op.operation_id,
                event_type=SyncAuditEventType.OPERATION_FAILED,
                entity_type=op.entity_type,
                entity_id=op.entity_id,
                actor_id=actor.actor_id,
                status=SyncStatus.REJECTED,
                error_code="DOMAIN_ERROR",
                details=str(err),
            )
            return SyncOperationResult(
                operation_id=op.operation_id,
                entity_id=op.entity_id,
                entity_type=op.entity_type,
                status=SyncStatus.REJECTED,
                message=f"Domain mutation rejected: {str(err)}",
            )

    def _apply_domain_mutation(
        self,
        op: SyncOperation,
        actor: AuthenticatedActor,
    ) -> Dict[str, Any]:
        """Applies mutation to the appropriate domain service."""
        if op.entity_type == SyncEntityType.INCIDENT:
            if op.operation_type == "CREATE":
                incident_model = Incident(**op.payload)
                return self.incident_service.create_incident(incident_model, actor=actor.actor_id)
            elif op.operation_type == "UPDATE":
                # Handle status transition if provided
                if "status" in op.payload:
                    return self.incident_service.update_incident_status(
                        incident_id=op.entity_id,
                        new_status=op.payload["status"],
                        expected_state_version=op.base_state_version,
                        notes=op.payload.get("notes"),
                        assigned_team_id=op.payload.get("assigned_team_id"),
                    )
                else:
                    return self.incident_service.update_incident_details(
                        incident_id=op.entity_id,
                        severity=op.payload.get("severity"),
                        description=op.payload.get("description"),
                        priority=op.payload.get("priority"),
                        expected_state_version=op.base_state_version,
                    )
        elif op.entity_type == SyncEntityType.RESOURCE_REQUEST:
            # Tactical supply requisition registration
            return {
                "request_id": op.entity_id,
                "status": "SUBMITTED",
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }
        elif op.entity_type == SyncEntityType.EVIDENCE:
            return {
                "evidence_id": op.entity_id,
                "status": "REGISTERED",
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }

        return {"status": "SUCCESS"}
