"""
Hospital REST API Endpoints.
Provides hospital registration, querying, filtering, capacity updates,
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
from services.api.app.schemas.hospital import (
    Hospital,
    HospitalStatus,
)
from services.api.app.schemas.road import Accessibility

router = APIRouter(prefix="/api/v1/hospitals", tags=["Hospitals"])

# Global singleton service instance
_facility_service = FacilityService()


def get_facility_service() -> FacilityService:
    return _facility_service


class HospitalCapacityUpdateRequest(BaseModel):
    available_capacity: int = Field(..., ge=0, description="Updated available bed count")
    capacity: Optional[int] = Field(None, ge=0, description="Updated total bed capacity")
    icu_available: Optional[int] = Field(None, ge=0, description="Updated available ICU beds")
    expected_state_version: Optional[int] = Field(None, description="Current known state version for optimistic concurrency")
    reason: Optional[str] = Field(None, description="Operational rationale for capacity adjustment")


class HospitalStatusUpdateRequest(BaseModel):
    status: HospitalStatus = Field(..., description="Target operational status")
    expected_state_version: Optional[int] = Field(None, description="Current known state version for optimistic concurrency")
    reason: Optional[str] = Field(None, description="Operational rationale for status change")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
def create_hospital(hospital: Hospital):
    """
    Register a new operational hospital or emergency trauma center.
    Validates GeoJSON location and bounds (0 <= available_capacity <= capacity).
    """
    service = get_facility_service()
    try:
        return service.create_hospital(hospital)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.get("", response_model=Dict[str, Any])
def list_hospitals(
    status_filter: Optional[HospitalStatus] = Query(None, alias="status"),
    accessibility_filter: Optional[Accessibility] = Query(None, alias="accessibility"),
    emergency_available: Optional[bool] = Query(None, alias="emergency_available"),
    has_available_capacity: Optional[bool] = Query(None, alias="has_available_capacity"),
    sort_by: str = Query("name", regex="^(name|available_capacity|updated_at|last_updated)$"),
    sort_desc: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Retrieve paginated operational hospitals with factual filtering,
    deterministic sorting, and active flood exposure status.
    """
    service = get_facility_service()
    return service.list_hospitals(
        status=status_filter,
        accessibility=accessibility_filter,
        emergency_available=emergency_available,
        has_available_capacity=has_available_capacity,
        sort_by=sort_by,
        sort_desc=sort_desc,
        limit=limit,
        offset=offset,
    )


@router.get("/{hospital_id}", response_model=Dict[str, Any])
def get_hospital(hospital_id: str):
    """
    Retrieve full operational details for a hospital, including flood exposure.
    """
    service = get_facility_service()
    try:
        return service.get_hospital(hospital_id)
    except FacilityNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.patch("/{hospital_id}/capacity", response_model=Dict[str, Any])
def update_hospital_capacity(hospital_id: str, request: HospitalCapacityUpdateRequest):
    """
    Update hospital capacity with optimistic concurrency validation.
    """
    service = get_facility_service()
    try:
        return service.update_hospital_capacity(
            hospital_id=hospital_id,
            new_available_capacity=request.available_capacity,
            new_total_capacity=request.capacity,
            new_icu_available=request.icu_available,
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


@router.patch("/{hospital_id}/status", response_model=Dict[str, Any])
def update_hospital_status(hospital_id: str, request: HospitalStatusUpdateRequest):
    """
    Update hospital status (OPERATIONAL, OVERLOADED, EVACUATING, CLOSED)
    with optimistic concurrency check and confirmation.
    """
    service = get_facility_service()
    try:
        return service.update_hospital_status(
            hospital_id=hospital_id,
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


@router.get("/{hospital_id}/history", response_model=List[Dict[str, Any]])
def get_hospital_history(hospital_id: str):
    """
    Retrieve chronological immutable audit log of all capacity and status updates.
    """
    service = get_facility_service()
    try:
        return service.get_hospital_history(hospital_id)
    except FacilityNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
