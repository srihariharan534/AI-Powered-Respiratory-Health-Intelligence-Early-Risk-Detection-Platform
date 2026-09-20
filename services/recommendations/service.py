"""
Recommendation Service & Lifecycle Authority (Phase 21).
Enforces:
- In-memory persistence of proposals with version immutability
- Centralized RecommendationStateMachine transitions
- Role-based authorization and actor audit tracking
- State version validation: blocks approval if Digital Twin state has advanced (stale recommendation protection)
- Operational precondition validation (incident resolution, facility capacity/closure, route status)
- Atomic approval and rejection executions with append-only audit persistence
- Concurrency safety and idempotency support
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional
from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.schemas.recommendation import (
    Recommendation,
    RecommendationApprovalStatus,
    RecommendationEntityType,
)
from services.recommendations.contracts import (
    AuditEventType,
    RecommendationAuditEntry,
    RecommendationAuditEvent,
    RecommendationDecisionRecord,
)
from services.recommendations.governance.audit_ledger import AuditLedger
from services.recommendations.governance.roles import (
    AuthenticatedActor,
    Permission,
    UserRole,
)
from services.recommendations.governance.state_machine import (
    GovernanceError,
    InvalidStateTransitionError,
    PreconditionFailedError,
    RecommendationStateMachine,
    StaleRecommendationError,
    UnauthorizedActionError,
)


class RecommendationNotFoundError(GovernanceError):
    """Raised when the requested recommendation ID is not found."""
    pass


class RecommendationService:
    """Manages recommendation lifecycle, preconditions, authorization, and audit ledger."""

    def __init__(
        self,
        digital_twin: DigitalTwinStateManager,
        audit_ledger: Optional[AuditLedger] = None,
        incident_service: Optional[Any] = None,
        facility_service: Optional[Any] = None,
    ) -> None:
        self.digital_twin = digital_twin
        self.audit_ledger = audit_ledger or AuditLedger()
        self.incident_service = incident_service
        self.facility_service = facility_service
        self._lock = threading.Lock()
        self._recommendations: Dict[str, Recommendation] = {}
        self._metadata_map: Dict[str, Dict[str, Any]] = {}

    def save_recommendation(
        self,
        rec: Recommendation,
        actor: Optional[AuthenticatedActor] = None,
        mode: str = "REAL_DATA",
        supersedes_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Recommendation:
        """Stores a generated recommendation and records creation in audit ledger."""
        with self._lock:
            stored_rec = rec.model_copy(deep=True)
            self._recommendations[rec.recommendation_id] = stored_rec
            self._metadata_map[rec.recommendation_id] = {
                "mode": mode,
                "supersedes_id": supersedes_id,
                **(metadata or {}),
            }

            # Record creation in audit ledger
            actor_id = actor.actor_id if actor else "SYSTEM"
            actor_role = actor.role.value if actor else UserRole.OPERATOR.value
            current_state_str = f"state-v{self.digital_twin.state_version}"

            self.audit_ledger.append_event(
                RecommendationAuditEvent(
                    event_type=AuditEventType.RECOMMENDATION_CREATED,
                    actor_id=actor_id,
                    actor_role=actor_role,
                    recommendation_id=rec.recommendation_id,
                    previous_state=None,
                    new_state=RecommendationApprovalStatus.PENDING,
                    reason=f"Generated recommendation {rec.action.value} targeting {rec.target.entity_id}",
                    source_state_version=rec.source_state_version,
                    current_state_version=current_state_str,
                    supersedes_recommendation_id=supersedes_id,
                    target_snapshot={
                        "entity_type": rec.target.entity_type.value,
                        "entity_id": rec.target.entity_id,
                        "description": rec.target.description,
                        "priority": rec.priority,
                        "mode": mode,
                    },
                )
            )
            return stored_rec.model_copy(deep=True)

    def get_recommendation(
        self,
        rec_id: str,
        actor: Optional[AuthenticatedActor] = None,
    ) -> Optional[Recommendation]:
        """Retrieves recommendation, marking EXPIRED if state has advanced."""
        with self._lock:
            rec = self._recommendations.get(rec_id)
            if not rec:
                return None

            current_state_str = f"state-v{self.digital_twin.state_version}"
            if rec.source_state_version != current_state_str and rec.approval_status == RecommendationApprovalStatus.PENDING:
                rec.approval_status = RecommendationApprovalStatus.EXPIRED
                self._record_expiration_event(
                    rec=rec,
                    actor_id="SYSTEM",
                    actor_role="SYSTEM",
                    reason=f"Digital Twin state advanced from {rec.source_state_version} to {current_state_str}",
                )

            # Record VIEWED audit event if actor provided
            if actor:
                self.audit_ledger.append_event(
                    RecommendationAuditEvent(
                        event_type=AuditEventType.RECOMMENDATION_VIEWED,
                        actor_id=actor.actor_id,
                        actor_role=actor.role.value,
                        recommendation_id=rec.recommendation_id,
                        previous_state=rec.approval_status,
                        new_state=rec.approval_status,
                        reason="Recommendation reviewed by operator",
                        source_state_version=rec.source_state_version,
                        current_state_version=current_state_str,
                    )
                )

            return rec.model_copy(deep=True)

    def list_recommendations(
        self,
        status: Optional[RecommendationApprovalStatus] = None,
        action: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> List[Recommendation]:
        """Lists recommendations with optional filtering."""
        with self._lock:
            current_state_str = f"state-v{self.digital_twin.state_version}"
            results = []

            for rec_id, rec in self._recommendations.items():
                # Auto-expire pending recommendations if state is stale
                if rec.source_state_version != current_state_str and rec.approval_status == RecommendationApprovalStatus.PENDING:
                    rec.approval_status = RecommendationApprovalStatus.EXPIRED
                    self._record_expiration_event(
                        rec=rec,
                        actor_id="SYSTEM",
                        actor_role="SYSTEM",
                        reason=f"Digital Twin state advanced from {rec.source_state_version} to {current_state_str}",
                    )

                if status and rec.approval_status != status:
                    continue
                if action and rec.action.value != action:
                    continue
                if mode:
                    rec_meta = self._metadata_map.get(rec_id, {})
                    if rec_meta.get("mode") != mode:
                        continue

                results.append(rec.model_copy(deep=True))

            return sorted(results, key=lambda r: r.created_at, reverse=True)

    def approve_recommendation(
        self,
        rec_id: str,
        actor: AuthenticatedActor,
        reason: str = "Authorized for operational response",
        idempotency_key: Optional[str] = None,
    ) -> Recommendation:
        """
        Approves a recommendation atomically.
        Enforces:
        1. Existence and state machine transition rules.
        2. RBAC authorization (actor must possess APPROVE_RECOMMENDATION permission).
        3. Human approval requirement (`requires_human_approval == True`).
        4. State version match (`source_state_version == current_state_version`).
        5. Simulation isolation (SIMULATION / DEMO cannot be approved as live operations).
        6. Operational preconditions (facility availability, incident active).
        7. Concurrency and idempotency.
        """
        # 1. Check idempotency cache first
        if idempotency_key:
            cached = self.audit_ledger.get_decision_by_idempotency_key(idempotency_key)
            if cached and cached.recommendation_id == rec_id:
                existing_rec = self._recommendations.get(rec_id)
                if existing_rec:
                    return existing_rec.model_copy(deep=True)

        with self._lock:
            # 2. Authorization check
            if not actor.has_permission(Permission.APPROVE_RECOMMENDATION):
                self._record_blocked_event(
                    rec_id=rec_id,
                    actor=actor,
                    reason=f"Actor '{actor.actor_id}' with role '{actor.role.value}' unauthorized to approve",
                )
                raise UnauthorizedActionError(
                    f"Role '{actor.role.value}' does not possess permission to approve recommendations."
                )

            rec = self._recommendations.get(rec_id)
            if not rec:
                raise RecommendationNotFoundError(f"Recommendation '{rec_id}' not found.")

            # 3. State machine validation
            RecommendationStateMachine.validate_transition(rec, RecommendationApprovalStatus.APPROVED)

            # 4. Enforce requires_human_approval
            if not rec.requires_human_approval:
                raise PreconditionFailedError(
                    f"Recommendation '{rec_id}' does not require human approval."
                )

            # 5. State freshness check
            current_state_str = f"state-v{self.digital_twin.state_version}"
            if rec.source_state_version != current_state_str:
                rec.approval_status = RecommendationApprovalStatus.EXPIRED
                self._record_blocked_event(
                    rec_id=rec_id,
                    actor=actor,
                    reason=f"State stale: source is {rec.source_state_version}, current is {current_state_str}",
                )
                self._record_expiration_event(
                    rec=rec,
                    actor_id=actor.actor_id,
                    actor_role=actor.role.value,
                    reason=f"Stale state invalidation upon approval attempt (current {current_state_str})",
                )
                raise StaleRecommendationError(
                    f"Cannot approve recommendation {rec_id}: source state is {rec.source_state_version}, "
                    f"but current state is {current_state_str}. Must regenerate recommendation against current state."
                )

            # 6. Operational Mode Check
            meta = self._metadata_map.get(rec_id, {})
            mode = meta.get("mode", "REAL_DATA")
            if mode in ("SIMULATION", "DEMO"):
                raise PreconditionFailedError(
                    f"Recommendation '{rec_id}' was generated under mode '{mode}' and cannot be approved for live operations."
                )

            # 7. Operational Preconditions Check (Incident & Facilities)
            self._validate_operational_preconditions(rec, current_state_str)

            # 8. Apply transition atomically
            previous_status = rec.approval_status
            rec.approval_status = RecommendationApprovalStatus.APPROVED
            rec.approved_by = actor.actor_id
            rec.approved_at = datetime.now(timezone.utc)

            # 9. Record in audit ledger
            audit_event = RecommendationAuditEvent(
                event_type=AuditEventType.RECOMMENDATION_APPROVED,
                actor_id=actor.actor_id,
                actor_role=actor.role.value,
                recommendation_id=rec_id,
                previous_state=previous_status,
                new_state=RecommendationApprovalStatus.APPROVED,
                reason=reason,
                source_state_version=rec.source_state_version,
                current_state_version=current_state_str,
                target_snapshot={
                    "target": rec.target.model_dump(),
                    "action": rec.action.value,
                    "priority": rec.priority,
                    "confidence": rec.confidence,
                },
            )
            self.audit_ledger.append_event(audit_event)

            # 10. Record durable decision record
            decision_record = RecommendationDecisionRecord(
                recommendation_id=rec_id,
                decision=RecommendationApprovalStatus.APPROVED,
                decision_reason=reason,
                decision_by=actor.actor_id,
                decision_by_role=actor.role.value,
                source_state_version=rec.source_state_version,
                current_state_version=current_state_str,
                idempotency_key=idempotency_key,
                recommendation_snapshot=rec.model_dump(),
            )
            self.audit_ledger.save_decision_record(decision_record)

            return rec.model_copy(deep=True)

    def reject_recommendation(
        self,
        rec_id: str,
        actor: AuthenticatedActor,
        reason: str,
        idempotency_key: Optional[str] = None,
    ) -> Recommendation:
        """Rejects a recommendation with mandatory justification and authorization check."""
        if not reason or len(reason.strip()) < 3:
            raise ValueError("A substantive decision_reason is mandatory when rejecting a recommendation.")

        if idempotency_key:
            cached = self.audit_ledger.get_decision_by_idempotency_key(idempotency_key)
            if cached and cached.recommendation_id == rec_id:
                existing_rec = self._recommendations.get(rec_id)
                if existing_rec:
                    return existing_rec.model_copy(deep=True)

        with self._lock:
            if not actor.has_permission(Permission.REJECT_RECOMMENDATION):
                self._record_blocked_event(
                    rec_id=rec_id,
                    actor=actor,
                    reason=f"Actor '{actor.actor_id}' with role '{actor.role.value}' unauthorized to reject",
                )
                raise UnauthorizedActionError(
                    f"Role '{actor.role.value}' does not possess permission to reject recommendations."
                )

            rec = self._recommendations.get(rec_id)
            if not rec:
                raise RecommendationNotFoundError(f"Recommendation '{rec_id}' not found.")

            # Validate state transition
            RecommendationStateMachine.validate_transition(rec, RecommendationApprovalStatus.REJECTED)

            current_state_str = f"state-v{self.digital_twin.state_version}"
            previous_status = rec.approval_status
            rec.approval_status = RecommendationApprovalStatus.REJECTED

            # Append audit event
            audit_event = RecommendationAuditEvent(
                event_type=AuditEventType.RECOMMENDATION_REJECTED,
                actor_id=actor.actor_id,
                actor_role=actor.role.value,
                recommendation_id=rec_id,
                previous_state=previous_status,
                new_state=RecommendationApprovalStatus.REJECTED,
                reason=reason,
                source_state_version=rec.source_state_version,
                current_state_version=current_state_str,
            )
            self.audit_ledger.append_event(audit_event)

            # Record durable decision record
            decision_record = RecommendationDecisionRecord(
                recommendation_id=rec_id,
                decision=RecommendationApprovalStatus.REJECTED,
                decision_reason=reason,
                decision_by=actor.actor_id,
                decision_by_role=actor.role.value,
                source_state_version=rec.source_state_version,
                current_state_version=current_state_str,
                idempotency_key=idempotency_key,
                recommendation_snapshot=rec.model_dump(),
            )
            self.audit_ledger.save_decision_record(decision_record)

            return rec.model_copy(deep=True)

    def expire_recommendation(
        self,
        rec_id: str,
        actor: AuthenticatedActor,
        reason: str,
    ) -> Recommendation:
        """Manually expires a recommendation (admin/system action)."""
        with self._lock:
            if not actor.has_permission(Permission.EXPIRE_RECOMMENDATION):
                raise UnauthorizedActionError(
                    f"Role '{actor.role.value}' does not possess permission to expire recommendations."
                )

            rec = self._recommendations.get(rec_id)
            if not rec:
                raise RecommendationNotFoundError(f"Recommendation '{rec_id}' not found.")

            RecommendationStateMachine.validate_transition(rec, RecommendationApprovalStatus.EXPIRED)

            current_state_str = f"state-v{self.digital_twin.state_version}"
            rec.approval_status = RecommendationApprovalStatus.EXPIRED
            self._record_expiration_event(
                rec=rec,
                actor_id=actor.actor_id,
                actor_role=actor.role.value,
                reason=reason,
            )
            return rec.model_copy(deep=True)

    def _validate_operational_preconditions(self, rec: Recommendation, current_state_str: str) -> None:
        """Verifies external operational entities still exist and remain eligible."""
        target = rec.target

        # Check Hospital
        if target.entity_type == RecommendationEntityType.HOSPITAL and self.facility_service:
            try:
                hosp_data = self.facility_service.get_hospital(target.entity_id)
                if hosp_data:
                    # Check status and capacity
                    status_val = hosp_data.get("status")
                    avail_cap = hosp_data.get("available_capacity", 0)
                    if status_val in ("CLOSED", "EVACUATING") or avail_cap <= 0:
                        rec.approval_status = RecommendationApprovalStatus.EXPIRED
                        raise PreconditionFailedError(
                            f"Target hospital '{target.entity_id}' is no longer operational (status={status_val}, available_capacity={avail_cap})."
                        )
            except Exception as e:
                if isinstance(e, PreconditionFailedError):
                    raise
                pass  # Fall through if service not configured

        # Check Shelter
        if target.entity_type == RecommendationEntityType.SHELTER and self.facility_service:
            try:
                shelter_data = self.facility_service.get_shelter(target.entity_id)
                if shelter_data:
                    status_val = shelter_data.get("status")
                    avail_cap = shelter_data.get("available_capacity", 0)
                    if status_val in ("CLOSED", "AT_CAPACITY") or avail_cap <= 0:
                        rec.approval_status = RecommendationApprovalStatus.EXPIRED
                        raise PreconditionFailedError(
                            f"Target shelter '{target.entity_id}' is no longer operational (status={status_val}, available_capacity={avail_cap})."
                        )
            except Exception as e:
                if isinstance(e, PreconditionFailedError):
                    raise
                pass

        # Check Incident if target is ZONE representing an incident
        if self.incident_service:
            # If target description or ID references an incident
            inc_id = target.entity_id if target.entity_id.startswith("INC-") else None
            if inc_id:
                try:
                    inc_data = self.incident_service.get_incident(inc_id)
                    if inc_data:
                        inc_status = inc_data.get("status")
                        if inc_status in ("RESOLVED", "CANCELLED"):
                            rec.approval_status = RecommendationApprovalStatus.EXPIRED
                            raise PreconditionFailedError(
                                f"Associated incident '{inc_id}' is already {inc_status}. Recommendation is obsolete."
                            )
                except Exception as e:
                    if isinstance(e, PreconditionFailedError):
                        raise
                    pass

    def _record_expiration_event(
        self,
        rec: Recommendation,
        actor_id: str,
        actor_role: str,
        reason: str,
    ) -> None:
        current_state_str = f"state-v{self.digital_twin.state_version}"
        self.audit_ledger.append_event(
            RecommendationAuditEvent(
                event_type=AuditEventType.RECOMMENDATION_EXPIRED,
                actor_id=actor_id,
                actor_role=actor_role,
                recommendation_id=rec.recommendation_id,
                previous_state=RecommendationApprovalStatus.PENDING,
                new_state=RecommendationApprovalStatus.EXPIRED,
                reason=reason,
                source_state_version=rec.source_state_version,
                current_state_version=current_state_str,
            )
        )

    def _record_blocked_event(
        self,
        rec_id: str,
        actor: AuthenticatedActor,
        reason: str,
    ) -> None:
        rec = self._recommendations.get(rec_id)
        src_ver = rec.source_state_version if rec else "unknown"
        current_state_str = f"state-v{self.digital_twin.state_version}"
        self.audit_ledger.append_event(
            RecommendationAuditEvent(
                event_type=AuditEventType.APPROVAL_BLOCKED,
                actor_id=actor.actor_id,
                actor_role=actor.role.value,
                recommendation_id=rec_id,
                previous_state=rec.approval_status if rec else None,
                new_state=rec.approval_status if rec else None,
                reason=reason,
                source_state_version=src_ver,
                current_state_version=current_state_str,
            )
        )

    def get_audit_log(self) -> List[RecommendationAuditEntry]:
        """Backwards compatibility helper returning legacy RecommendationAuditEntry list."""
        events = self.audit_ledger.list_events(limit=500)
        entries = []
        for e in events:
            if e.new_state in (RecommendationApprovalStatus.APPROVED, RecommendationApprovalStatus.REJECTED):
                rec = self._recommendations.get(e.recommendation_id)
                action_str = rec.action.value if rec else "OPERATIONAL_ACTION"
                entries.append(
                    RecommendationAuditEntry(
                        recommendation_id=e.recommendation_id,
                        action=action_str,
                        decision=e.new_state,
                        decision_timestamp=e.timestamp,
                        decision_by=e.actor_id,
                        source_state_version=e.source_state_version,
                        current_state_version=e.current_state_version,
                        reason=e.reason,
                    )
                )
        return entries
