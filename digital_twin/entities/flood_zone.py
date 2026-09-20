"""
NEXUS Digital Twin - Flood Zone Entity.
Spatial flood state representation in the operational twin.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class FloodSeverity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    EXTREME = "EXTREME"


class FloodZoneEntity(BaseModel):
    """
    Operational representation of a flood zone.
    CRITICAL: Does NOT predict or simulate flood propagation.
    Stores observed/reported spatial flood extents and water depths.
    Unknown values must remain distinguishable from zero.
    """
    flood_zone_id: str = Field(..., description="Unique flood zone identifier (e.g. 'FZ-001')")
    name: Optional[str] = Field(None, description="Descriptive zone name or river basin")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON polygon or multi-polygon geometry")
    severity: FloodSeverity = Field(..., description="Flood severity category")
    water_depth_m: Optional[float] = Field(None, description="Observed depth in meters; None means unknown, distinct from 0.0", ge=0.0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp (UTC)")
    source: str = Field(default="SYSTEM", description="Source of flood data (e.g. SATELLITE, GAUGE, SIMULATION)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

    model_config = {
        "frozen": False,
        "validate_assignment": True,
    }
