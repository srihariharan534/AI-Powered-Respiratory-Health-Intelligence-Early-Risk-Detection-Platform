"""
Operational Recommendations & Human Governance REST API Endpoints (Phases 20 & 21).
Provides:
- GET  /api/v1/recommendations: List recommendations with filtering
- GET  /api/v1/recommendations/{id}: Get recommendation details
- POST /api/v1/recommendations/generate: Generate recommendations on-demand (operator/commander)
- POST /api/v1/recommendations/{id}/approve: Human coordinator approval with RBAC & state freshness checks
- POST /api/v1/recommendations/{id}/reject: Human coordinator rejection with mandatory justification & audit logging
- POST /api/v1/recommendations/{id}/expire: Administrative explicit expiration
- GET  /api/v1/recommendations/{id}/audit: Audit history for specific recommendation
- GET  /api/v1/recommendations/audit/ledger: Retrieve chronological audit event stream
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.repositories.facility_service import FacilityService
from services.api.app.repositories.incident_service import IncidentService
from services.api.app.schemas.hospital import Hospital
from services.api.app.schemas.incident import Incident
from services.api.app.schemas.shelter import Shelter
from services.api.app.schemas.recommendation import (
    Recommendation,
    RecommendationApprovalStatus,
)
from services.recommendations.contracts import (
    AuditEventType,
    GenerateRecommendationRequest,
    RecommendationAuditEntry,
    RecommendationAuditEvent,
)
from services.recommendations.engine import OperationalRecommendationEngine
from services.recommendations.governance.audit_ledger import AuditLedger
from services.recommendations.governance.roles import (
    AuthenticatedActor,
    Permission,
    UserRole,
    get_current_actor,
)
from services.recommendations.governance.state_machine import (
    GovernanceError,
    InvalidStateTransitionError,
    PreconditionFailedError,
    StaleRecommendationError,
    UnauthorizedActionError,
)
from services.recommendations.service import (
    RecommendationNotFoundError,
    RecommendationService,
)

router = APIRouter(prefix="/api/v1/recommendations", tags=["Operational Recommendations"])

# Single shared instances
_dt_state_manager = DigitalTwinStateManager()
_incident_service = IncidentService(digital_twin=_dt_state_manager)
_facility_service = FacilityService(digital_twin=_dt_state_manager)
_audit_ledger = AuditLedger()
_recommendation_engine = OperationalRecommendationEngine(digital_twin=_dt_state_manager)
_recommendation_service = RecommendationService(
    digital_twin=_dt_state_manager,
    audit_ledger=_audit_ledger,
    incident_service=_incident_service,
    facility_service=_facility_service,
)


def get_dt_state_manager() -> DigitalTwinStateManager:
    return _dt_state_manager


def get_audit_ledger() -> AuditLedger:
    return _audit_ledger


def get_recommendation_service() -> RecommendationService:
    return _recommendation_service


def get_recommendation_engine() -> OperationalRecommendationEngine:
    return _recommendation_engine


class DecisionActionPayload(BaseModel):
    actor: Optional[str] = Field(None, description="Optional callsign (if omitted, extracted from X-Actor-Id header)")
    reason: str = Field(..., min_length=3, description="Operational justification for approval/rejection")
    idempotency_key: Optional[str] = Field(None, description="Client idempotency token to prevent duplicate decisions")


@router.get("", response_model=List[Recommendation], summary="List recommendations with filtering")
def list_recommendations(
    status: Optional[RecommendationApprovalStatus] = None,
    action: Optional[str] = None,
    mode: Optional[str] = None,
    actor: AuthenticatedActor = Depends(get_current_actor),
):
    """List operational recommendations matching criteria."""
    svc = get_recommendation_service()
    return svc.list_recommendations(status=status, action=action, mode=mode)


@router.get("/{recommendation_id}", response_model=Recommendation, summary="Get recommendation by ID")
def get_recommendation(
    recommendation_id: str,
    actor: AuthenticatedActor = Depends(get_current_actor),
):
    """Retrieve an individual recommendation."""
    svc = get_recommendation_service()
    rec = svc.get_recommendation(recommendation_id, actor=actor)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found.",
        )
    return rec


@router.post("/generate", response_model=List[Recommendation], summary="Generate operational recommendations")
def generate_recommendations(
    request: GenerateRecommendationRequest,
    actor: AuthenticatedActor = Depends(get_current_actor),
):
    """
    On-demand operational recommendation generation.
    Evaluates current Digital Twin state, facilities, and active incidents.
    Requires GENERATE_RECOMMENDATIONS permission.
    """
    if not actor.has_permission(Permission.GENERATE_RECOMMENDATIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Actor role '{actor.role.value}' is unauthorized to generate recommendations.",
        )

    engine = get_recommendation_engine()
    svc = get_recommendation_service()

    # Load active incidents and facilities from repositories
    raw_incidents = _incident_service.list_incidents().get("items", [])
    raw_hospitals = _facility_service.list_hospitals().get("items", [])
    raw_shelters = _facility_service.list_shelters().get("items", [])

    incidents = [Incident.model_validate(i) for i in raw_incidents]
    hospitals = [Hospital.model_validate(h) for h in raw_hospitals]
    shelters = [Shelter.model_validate(s) for s in raw_shelters]

    # Provide default operational data if empty (e.g. fresh startup/tests)
    if not incidents:
        from services.api.app.schemas.incident import IncidentEventType, IncidentSeverity, IncidentSource, IncidentStatus, PointLocation
        demo_inc = Incident(
            incident_id="INC-DEFAULT-001",
            description="Active river inundation cluster",
            event_type=IncidentEventType.FLOOD_INUNDATION,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            priority=1,
            location=PointLocation(coordinates=[80.2707, 13.0827]),
            reported_at=datetime.now(timezone.utc),
            reported_by="COORDINATOR_SYSTEM",
            source=IncidentSource.FIELD_OFFICER,
        )
        incidents.append(demo_inc)

    if not hospitals:
        from services.api.app.schemas.hospital import HospitalSource, HospitalStatus
        from services.api.app.schemas.road import Accessibility
        demo_hosp = Hospital(
            hospital_id="H-DEFAULT-001",
            name="District General Hospital",
            location=PointLocation(coordinates=[80.2750, 13.0850]),
            capacity=100,
            available_capacity=25,
            emergency_available=True,
            status=HospitalStatus.OPERATIONAL,
            accessibility=Accessibility.ALL_VEHICLES,
            last_updated=datetime.now(timezone.utc),
            source=HospitalSource.SYNTHETIC_DEMO,
        )
        hospitals.append(demo_hosp)

    generated = engine.generate_recommendations(
        request=request,
        incidents=incidents,
        hospitals=hospitals,
        shelters=shelters,
    )

    # Persist in service with creation audit events
    for rec in generated:
        svc.save_recommendation(rec, actor=actor, mode=request.mode)

    return generated


@router.post("/{recommendation_id}/approve", response_model=Recommendation, summary="Approve recommendation")
def approve_recommendation(
    recommendation_id: str,
    payload: DecisionActionPayload,
    actor: AuthenticatedActor = Depends(get_current_actor),
):
    """
    Approve an operational recommendation.
    Enforces RBAC authorization, state version validation, and operational preconditions.
    """
    effective_actor = AuthenticatedActor(
        actor_id=payload.actor or actor.actor_id,
        role=actor.role,
    )
    svc = get_recommendation_service()
    try:
        return svc.approve_recommendation(
            rec_id=recommendation_id,
            actor=effective_actor,
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
        )
    except RecommendationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found.",
        )
    except UnauthorizedActionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        )
    except StaleRecommendationError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )
    except (InvalidStateTransitionError, PreconditionFailedError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.post("/{recommendation_id}/reject", response_model=Recommendation, summary="Reject recommendation")
def reject_recommendation(
    recommendation_id: str,
    payload: DecisionActionPayload,
    actor: AuthenticatedActor = Depends(get_current_actor),
):
    """Reject an operational recommendation with mandatory justification."""
    effective_actor = AuthenticatedActor(
        actor_id=payload.actor or actor.actor_id,
        role=actor.role,
    )
    svc = get_recommendation_service()
    try:
        return svc.reject_recommendation(
            rec_id=recommendation_id,
            actor=effective_actor,
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
        )
    except RecommendationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found.",
        )
    except UnauthorizedActionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        )
    except InvalidStateTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.post("/{recommendation_id}/expire", response_model=Recommendation, summary="Expire recommendation")
def expire_recommendation(
    recommendation_id: str,
    payload: DecisionActionPayload,
    actor: AuthenticatedActor = Depends(get_current_actor),
):
    """Explicitly expire a recommendation (administrative/system action)."""
    effective_actor = AuthenticatedActor(
        actor_id=payload.actor or actor.actor_id,
        role=actor.role,
    )
    svc = get_recommendation_service()
    try:
        return svc.expire_recommendation(
            rec_id=recommendation_id,
            actor=effective_actor,
            reason=payload.reason,
        )
    except RecommendationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found.",
        )
    except UnauthorizedActionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        )
    except InvalidStateTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.get("/{recommendation_id}/audit", response_model=List[RecommendationAuditEvent], summary="Get audit events for recommendation")
def get_recommendation_audit_events(
    recommendation_id: str,
    actor: AuthenticatedActor = Depends(get_current_actor),
):
    """Retrieve all chronological audit events associated with a specific recommendation."""
    ledger = get_audit_ledger()
    return ledger.list_events(recommendation_id=recommendation_id)


@router.get("/audit/ledger", response_model=List[RecommendationAuditEvent], summary="Get full audit ledger")
def get_full_audit_ledger(
    event_type: Optional[AuditEventType] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    actor: AuthenticatedActor = Depends(get_current_actor),
):
    """Retrieve immutable chronological audit ledger of recommendation decisions."""
    ledger = get_audit_ledger()
    return ledger.list_events(event_type=event_type, limit=limit, offset=offset)
