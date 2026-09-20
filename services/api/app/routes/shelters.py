"""
Shelter REST API Endpoints.
Provides shelter registration, querying, filtering, capacity updates,
status transitions, and chronological audit trail logs.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from services.api.app.repositories.facility_service import (
    FacilityNotFoundError,
    FacilityService,
    FacilityStateVersionConflictError,
)
from services.api.app.routes.hospitals import get_facility_service
from services.api.app.schemas.road import Accessibility
from services.api.app.schemas.shelter import (
    Shelter,
    ShelterStatus,
)

router = APIRouter(prefix="/api/v1/shelters", tags=["Shelters"])


class ShelterCapacityUpdateRequest(BaseModel):
    available_capacity: int = Field(..., ge=0, description="Updated available shelter occupancy spots")
    capacity: Optional[int] = Field(None, ge=0, description="Updated total capacity")
    expected_state_version: Optional[int] = Field(None, description="Current known state version for optimistic concurrency")
    reason: Optional[str] = Field(None, description="Operational rationale for capacity adjustment")


class ShelterStatusUpdateRequest(BaseModel):
    status: ShelterStatus = Field(..., description="Target operational status")
    expected_state_version: Optional[int] = Field(None, description="Current known state version for optimistic concurrency")
    reason: Optional[str] = Field(None, description="Operational rationale for status change")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
def create_shelter(shelter: Shelter):
    """
    Register a new evacuation shelter or relief camp.
    Validates GeoJSON location and bounds (0 <= available_capacity <= capacity).
    """
    service = get_facility_service()
    try:
        return service.create_shelter(shelter)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.get("", response_model=Dict[str, Any])
def list_shelters(
    status_filter: Optional[ShelterStatus] = Query(None, alias="status"),
    accessibility_filter: Optional[Accessibility] = Query(None, alias="accessibility"),
    has_available_capacity: Optional[bool] = Query(None, alias="has_available_capacity"),
    sort_by: str = Query("name", regex="^(name|available_capacity|updated_at|last_updated)$"),
    sort_desc: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Retrieve paginated operational shelters with factual filtering,
    deterministic sorting, and active flood exposure status.
    """
    service = get_facility_service()
    return service.list_shelters(
        status=status_filter,
        accessibility=accessibility_filter,
        has_available_capacity=has_available_capacity,
        sort_by=sort_by,
        sort_desc=sort_desc,
        limit=limit,
        offset=offset,
    )


@router.get("/{shelter_id}", response_model=Dict[str, Any])
def get_shelter(shelter_id: str):
    """
    Retrieve full operational details for a shelter, including flood exposure.
    """
    service = get_facility_service()
    try:
        return service.get_shelter(shelter_id)
    except FacilityNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.patch("/{shelter_id}/capacity", response_model=Dict[str, Any])
def update_shelter_capacity(shelter_id: str, request: ShelterCapacityUpdateRequest):
    """
    Update shelter capacity with optimistic concurrency validation.
    """
    service = get_facility_service()
    try:
        return service.update_shelter_capacity(
            shelter_id=shelter_id,
            new_available_capacity=request.available_capacity,
            new_total_capacity=request.capacity,
            expected_state_version=request.expected_state_version,
            reason=request.reason,
        )
    except FacilityNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except FacilityStateVersionConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "STATE_VERSION_CONFLICT",
                "message": str(err),
                "expected_version": err.expected_version,
                "current_version": err.current_version,
            },
        )


@router.patch("/{shelter_id}/status", response_model=Dict[str, Any])
def update_shelter_status(shelter_id: str, request: ShelterStatusUpdateRequest):
    """
    Update shelter status (OPEN, AT_CAPACITY, STANDBY, CLOSED)
    with optimistic concurrency check and confirmation.
    """
    service = get_facility_service()
    try:
        return service.update_shelter_status(
            shelter_id=shelter_id,
            new_status=request.status,
            expected_state_version=request.expected_state_version,
            reason=request.reason,
        )
    except FacilityNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except FacilityStateVersionConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "STATE_VERSION_CONFLICT",
                "message": str(err),
                "expected_version": err.expected_version,
                "current_version": err.current_version,
            },
        )


@router.get("/{shelter_id}/history", response_model=List[Dict[str, Any]])
def get_shelter_history(shelter_id: str):
    """
    Retrieve chronological immutable audit log of all capacity and status updates.
    """
    service = get_facility_service()
    try:
        return service.get_shelter_history(shelter_id)
    except FacilityNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
