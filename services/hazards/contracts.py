"""
Hazard-Agnostic Emergency Core Contracts (Multi-Emergency Platform).
Defines common EmergencyEvent, EmergencyType enum (12 disaster domains),
and HazardModule protocol interface.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, ConfigDict, Field


class EmergencyType(str, Enum):
    FLOOD = "FLOOD"
    CYCLONE = "CYCLONE"
    LANDSLIDE = "LANDSLIDE"
    WILDFIRE = "WILDFIRE"
    EXTREME_HEAT = "EXTREME_HEAT"
    TORNADO = "TORNADO"
    SEVERE_STORM = "SEVERE_STORM"
    INDUSTRIAL_ACCIDENT = "INDUSTRIAL_ACCIDENT"
    CHEMICAL_INCIDENT = "CHEMICAL_INCIDENT"
    URBAN_INFRASTRUCTURE_FAILURE = "URBAN_INFRASTRUCTURE_FAILURE"
    PUBLIC_HEALTH_EMERGENCY = "PUBLIC_HEALTH_EMERGENCY"
    MAJOR_TRANSPORT_INCIDENT = "MAJOR_TRANSPORT_INCIDENT"
    EARTHQUAKE = "EARTHQUAKE"


class EmergencySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EmergencyStatus(str, Enum):
    DETECTED = "DETECTED"
    ACTIVE = "ACTIVE"
    CONTAINED = "CONTAINED"
    RESOLVED = "RESOLVED"
    MONITORING = "MONITORING"


class ModuleMaturity(str, Enum):
    VALIDATED = "VALIDATED"          # Fully validated with physical models & benchmark datasets (e.g. Flood)
    IMPLEMENTED = "IMPLEMENTED"      # Functional logic, schemas, and tests present
    ARCHITECTURE_READY = "ARCHITECTURE_READY"  # Domain contracts & mock pipelines ready
    EXPERIMENTAL = "EXPERIMENTAL"


class EmergencyEvent(BaseModel):
    """Common emergency abstraction connecting all disaster domains to the single Digital Twin."""
    model_config = ConfigDict(extra="forbid")

    emergency_id: str = Field(..., min_length=3)
    emergency_type: EmergencyType
    severity: EmergencySeverity
    status: EmergencyStatus
    location: Dict[str, Any] = Field(..., description="GeoJSON Point or Polygon")
    affected_area_km2: Optional[float] = None
    detected_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = Field(default="EMERGENCY_TELEMETRY")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    observations: Dict[str, Any] = Field(default_factory=dict)
    hazard_specific_params: Dict[str, Any] = Field(default_factory=dict)
    state_version: int = Field(default=1, ge=1)


class HazardRiskResult(BaseModel):
    hazard_type: EmergencyType
    risk_score: float = Field(..., ge=0.0, le=1.0)
    exposure_score: float = Field(..., ge=0.0, le=1.0)
    vulnerability_score: float = Field(..., ge=0.0, le=1.0)
    factors: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    maturity: ModuleMaturity


@runtime_checkable
class HazardModule(Protocol):
    """Protocol for all emergency domain plugins."""

    def get_emergency_type(self) -> EmergencyType: ...

    def get_maturity(self) -> ModuleMaturity: ...

    def calculate_risk(self, event: EmergencyEvent, context: Dict[str, Any]) -> HazardRiskResult: ...

    def generate_constraints(self, event: EmergencyEvent) -> Dict[str, Any]: ...

    def get_required_resources(self, event: EmergencyEvent) -> List[str]: ...
