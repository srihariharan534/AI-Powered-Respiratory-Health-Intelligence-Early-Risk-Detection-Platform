"""
NEXUS Digital Twin - Flood Updated Event.
Ingestion of observed or verified spatial flood changes into the Digital Twin.
"""

from typing import Any, Dict, Optional

from pydantic import Field

from digital_twin.entities.flood_zone import FloodSeverity
from digital_twin.events.base import TwinEvent


class FloodUpdatedEvent(TwinEvent):
    """
    Emitted when an observed flood extent or water depth changes.
    Does NOT predict future flood behavior. Unknown values remain None.
    """
    event_type: str = Field(default="FLOOD_UPDATED")
    flood_zone_id: str = Field(..., description="Target flood zone identifier")
    name: Optional[str] = Field(None, description="Optional descriptive name")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON polygon or multi-polygon boundary")
    severity: FloodSeverity = Field(..., description="Observed flood severity level")
    water_depth_m: Optional[float] = Field(None, description="Observed water depth; None = unknown, distinct from 0.0", ge=0.0)
