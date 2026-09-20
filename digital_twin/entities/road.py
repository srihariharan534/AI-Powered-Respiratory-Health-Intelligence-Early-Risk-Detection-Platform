"""
NEXUS Digital Twin - Road Entity.
Operational state of road segments in the emergency environment.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from services.api.app.schemas.road import Accessibility, RoadStatus


class RoadEntity(BaseModel):
    """
    Operational representation of a road segment.
    Note: Geographic/graph topology is managed by Phase 05/Phase 06.
    The Digital Twin tracks operational status, accessibility, and dynamic attributes.
    """
    road_id: str = Field(..., description="Unique road segment identifier (e.g. 'R-001')")
    name: Optional[str] = Field(None, description="Human-readable road name")
    status: RoadStatus = Field(default=RoadStatus.OPEN, description="Operational status: OPEN, RESTRICTED, BLOCKED, UNKNOWN")
    accessibility: Accessibility = Field(default=Accessibility.ALL_VEHICLES, description="Vehicle accessibility level")
    speed_kmh: Optional[float] = Field(None, description="Operational speed limit or observed speed in km/h", ge=0.0)
    associated_bridge_ids: List[str] = Field(default_factory=list, description="IDs of bridges carrying or traversing this road")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of last state update (UTC)")
    source: str = Field(default="SYSTEM", description="Source of last update (e.g., FIELD_REPORT, SIMULATION)")
    reason: Optional[str] = Field(None, description="Reason for current operational state")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary non-identifying operational metadata")

    model_config = {
        "frozen": False,
        "validate_assignment": True,
    }
