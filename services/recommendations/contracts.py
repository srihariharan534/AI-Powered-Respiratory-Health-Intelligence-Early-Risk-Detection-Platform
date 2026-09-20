"""
Data Contracts for NEXUS Operational Recommendation Engine & Governance (Phases 20 & 21).
Defines request payloads, candidate structures, audit events, decision records, and filters.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from services.api.app.schemas.recommendation import (
    DecisionFactor,
    Recommendation,
    RecommendationAction,
    RecommendationApprovalStatus,
    RecommendationEntityType,
    RecommendationTarget,
    RecommendationUncertainty,
)


class RecommendationType(str, Enum):
    INCIDENT_PRIORITY = "incident_priority"
    EVACUATION_ROUTE = "evacuation_route"
    HOSPITAL_SELECTION = "hospital_selection"
    SHELTER_SELECTION = "shelter_selection"
    RESOURCE_ALLOCATION = "resource_allocation"


class AuditEventType(str, Enum):
    RECOMMENDATION_CREATED = "RECOMMENDATION_CREATED"
    RECOMMENDATION_VIEWED = "RECOMMENDATION_VIEWED"
    RECOMMENDATION_APPROVED = "RECOMMENDATION_APPROVED"
    RECOMMENDATION_REJECTED = "RECOMMENDATION_REJECTED"
    RECOMMENDATION_EXPIRED = "RECOMMENDATION_EXPIRED"
    APPROVAL_BLOCKED = "APPROVAL_BLOCKED"


class GenerateRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recommendation_type: RecommendationType
    incident_id: Optional[str] = Field(None, description="Target incident identifier if applicable")
    entity_id: Optional[str] = Field(None, description="Optional facility or road ID if targeted directly")
    risk_model_version: str = Field(default="baseline-logistic-regression-v1", description="Model version used for risk input")
    policy_version: str = Field(default="policy-v1.0", description="Scoring policy weight set")
    scenario_id: Optional[str] = Field(None, description="What-if scenario ID if running in simulation mode")
    mode: str = Field(default="REAL_DATA", description="Operational execution mode: REAL_DATA, SIMULATION, DEMO")


class ScoredCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    entity_type: RecommendationEntityType
    entity_name: str
    total_score: float = Field(..., ge=0.0, le=1.0)
    hard_constraints_passed: bool
    rejection_reason: Optional[str] = None
    factors: List[DecisionFactor] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecommendationAuditEvent(BaseModel):
    """
    Canonical append-only audit event for recommendation governance (Phase 21).
    """
    model_config = ConfigDict(extra="forbid")
    audit_event_id: str = Field(default_factory=lambda: f"AUD-{uuid.uuid4().hex[:12]}")
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str
    actor_role: str
    recommendation_id: str
    previous_state: Optional[RecommendationApprovalStatus] = None
    new_state: Optional[RecommendationApprovalStatus] = None
    reason: str
    source_state_version: str
    current_state_version: str
    model_version: Optional[str] = None
    policy_version: Optional[str] = None
    supersedes_recommendation_id: Optional[str] = None
    target_snapshot: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Backwards compatibility alias for Phase 20 code
class RecommendationAuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recommendation_id: str
    action: str
    decision: RecommendationApprovalStatus
    decision_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision_by: str
    source_state_version: str
    current_state_version: str
    reason: str


class RecommendationDecisionRecord(BaseModel):
    """
    Durable decision record preserving historical context of approved or rejected recommendations.
    """
    model_config = ConfigDict(extra="forbid")
    decision_id: str = Field(default_factory=lambda: f"DEC-{uuid.uuid4().hex[:10]}")
    recommendation_id: str
    decision: RecommendationApprovalStatus
    decision_reason: str
    decision_by: str
    decision_by_role: str
    decision_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_state_version: str
    current_state_version: str
    policy_version: str = "policy-v1.0"
    model_version: str = "baseline-logistic-regression-v1"
    idempotency_key: Optional[str] = None
    recommendation_snapshot: Dict[str, Any]
