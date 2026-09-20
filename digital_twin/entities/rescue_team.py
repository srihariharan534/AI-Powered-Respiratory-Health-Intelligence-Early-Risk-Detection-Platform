"""
NEXUS Digital Twin - Rescue Team Entity.
Operational readiness and deployment state of emergency response units.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RescueTeamStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DISPATCHED = "DISPATCHED"
    ON_SCENE = "ON_SCENE"
    RETURNING = "RETURNING"
    OFF_DUTY = "OFF_DUTY"
    MAINTENANCE = "MAINTENANCE"


class RescueTeamEntity(BaseModel):
    """
    Operational representation of a rescue team unit.
    Note: Autonomous dispatch / resource optimization is out of scope for Phase 09.
    """
    rescue_team_id: str = Field(..., description="Unique team identifier (e.g. 'T-001')")
    name: Optional[str] = Field(None, description="Team unit name or callsign")
    status: RescueTeamStatus = Field(default=RescueTeamStatus.AVAILABLE, description="Operational status")
    location: Optional[Dict[str, Any]] = Field(None, description="Current coordinates or GeoJSON location")
    vehicle_type: Optional[str] = Field(None, description="Vehicle type (e.g., BOAT, 4X4, AMBULANCE)")
    capacity: int = Field(default=4, description="Evacuation/transport capacity per trip", ge=1)
    current_assignment: Optional[str] = Field(None, description="Assigned incident ID or mission ID")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of last update (UTC)")
    source: str = Field(default="SYSTEM", description="Source of update")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

    model_config = {
        "frozen": False,
        "validate_assignment": True,
    }
