"""
Multi-Emergency REST API Endpoints.
Allows querying supported hazards, calculating domain-specific risk, and inspecting constraints.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.hazards.contracts import (
    EmergencyEvent,
    EmergencySeverity,
    EmergencyStatus,
    EmergencyType,
    HazardRiskResult,
)
from services.hazards.registry import HazardRegistry

router = APIRouter(prefix="/api/v1/hazards", tags=["Multi-Emergency Domains"])

_registry = HazardRegistry()


def get_hazard_registry() -> HazardRegistry:
    return _registry


@router.get("", response_model=List[Dict[str, str]])
def list_supported_emergencies() -> List[Dict[str, str]]:
    """
    Lists all 12 supported emergency domains with their respective validation maturity.
    """
    return _registry.list_supported_emergencies()


@router.post("/evaluate", response_model=HazardRiskResult)
def evaluate_emergency_risk(event: EmergencyEvent) -> HazardRiskResult:
    """
    Evaluates risk and exposure for any of the 12 emergency types through its dedicated module.
    """
    try:
        mod = _registry.get_module(event.emergency_type)
        return mod.calculate_risk(event, {})
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to evaluate hazard '{event.emergency_type.value}': {str(err)}",
        )


@router.get("/{emergency_type}/resources", response_model=List[str])
def get_hazard_resources(emergency_type: EmergencyType) -> List[str]:
    """
    Retrieves recommended resource requirements for a specific hazard domain.
    """
    mod = _registry.get_module(emergency_type)
    dummy_event = EmergencyEvent(
        emergency_id="DUMMY",
        emergency_type=emergency_type,
        severity=EmergencySeverity.HIGH,
        status=EmergencyStatus.ACTIVE,
        location={"type": "Point", "coordinates": [80.22, 13.01]},
    )
    return mod.get_required_resources(dummy_event)
