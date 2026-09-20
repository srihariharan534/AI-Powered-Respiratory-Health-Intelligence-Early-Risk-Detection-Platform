"""
Incident REST API Endpoints.
Provides incident registration, querying, filtering, lifecycle transitions, and audit logs.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from services.api.app.repositories.incident_service import (
    IncidentNotFoundError,
    IncidentService,
    StateVersionConflictError,
)
from services.api.app.schemas.incident import (
    Incident,
    IncidentEventType,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from services.api.app.schemas.incident_lifecycle import InvalidIncidentTransitionError

router = APIRouter(prefix="/api/v1/incidents", tags=["Incidents"])

# Shared global service instance
_incident_service = IncidentService()


def get_incident_service() -> IncidentService:
    return _incident_service


class StatusTransitionRequest(BaseModel):
    new_status: IncidentStatus
    expected_state_version: Optional[int] = Field(None, description="Current known state version for optimistic concurrency")
    notes: Optional[str] = Field(None, description="Operational transition rationale")
    assigned_team_id: Optional[str] = Field(None, description="Assigned rescue team unit")


class IncidentUpdateRequest(BaseModel):
    severity: Optional[IncidentSeverity] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    expected_state_version: Optional[int] = None


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
def create_incident(incident: Incident):
    """
    Create a new operational emergency incident.
    Validates GeoJSON location and synchronizes with Digital Twin authority.
    """
    service = get_incident_service()
    try:
        return service.create_incident(incident)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.get("", response_model=Dict[str, Any])
def list_incidents(
    status_filter: Optional[IncidentStatus] = Query(None, alias="status"),
    severity_filter: Optional[IncidentSeverity] = Query(None, alias="severity"),
    event_type_filter: Optional[IncidentEventType] = Query(None, alias="event_type"),
    source_filter: Optional[IncidentSource] = Query(None, alias="source"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Retrieve paginated operational incidents with optional filtering.
    """
    service = get_incident_service()
    return service.list_incidents(
        status=status_filter,
        severity=severity_filter,
        event_type=event_type_filter,
        source=source_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/{incident_id}", response_model=Dict[str, Any])
def get_incident(incident_id: str):
    """
    Retrieve full details for an incident, including allowed lifecycle transitions.
    """
    service = get_incident_service()
    try:
        return service.get_incident(incident_id)
    except IncidentNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.patch("/{incident_id}", response_model=Dict[str, Any])
def update_incident_details(incident_id: str, update: IncidentUpdateRequest):
    """
    Update mutable incident attributes with optimistic concurrency validation.
    """
    service = get_incident_service()
    try:
        return service.update_incident_details(
            incident_id=incident_id,
            severity=update.severity,
            description=update.description,
            priority=update.priority,
            expected_state_version=update.expected_state_version,
        )
    except IncidentNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except StateVersionConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "STATE_VERSION_CONFLICT",
                "message": str(err),
                "current_state_version": err.current_version,
            },
        )


@router.post("/{incident_id}/transition", response_model=Dict[str, Any])
def transition_incident_status(incident_id: str, request: StatusTransitionRequest):
    """
    Transition incident operational status following the strict lifecycle state machine.
    """
    service = get_incident_service()
    try:
        return service.update_incident_status(
            incident_id=incident_id,
            new_status=request.new_status,
            expected_state_version=request.expected_state_version,
            notes=request.notes,
            assigned_team_id=request.assigned_team_id,
        )
    except IncidentNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except InvalidIncidentTransitionError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    except StateVersionConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "STATE_VERSION_CONFLICT",
                "message": str(err),
                "current_state_version": err.current_version,
            },
        )


@router.get("/{incident_id}/history", response_model=List[Dict[str, Any]])
def get_incident_audit_history(incident_id: str):
    """
    Retrieve chronological audit trail of all lifecycle events and state transitions.
    """
    service = get_incident_service()
    try:
        return service.get_incident_history(incident_id)
    except IncidentNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
