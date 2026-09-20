"""
NEXUS Digital Twin - Road and Bridge Status Changed Events.
Operational state transitions affecting road segments and bridges.
"""

from typing import Optional

from pydantic import Field

from digital_twin.entities.bridge import BridgeStatus
from digital_twin.events.base import TwinEvent
from services.api.app.schemas.road import Accessibility, RoadStatus


class RoadStatusChangedEvent(TwinEvent):
    """
    Emitted when a road's operational status, accessibility, or speed changes.
    Directly updates the Digital Twin entity and propagates to the Phase 08 routing overlay.
    """
    event_type: str = Field(default="ROAD_STATUS_CHANGED")
    road_id: str = Field(..., description="Target road identifier")
    previous_status: Optional[RoadStatus] = Field(None, description="Known previous status if available")
    new_status: RoadStatus = Field(..., description="Target new operational status")
    new_accessibility: Optional[Accessibility] = Field(None, description="Updated accessibility constraint")
    new_speed_kmh: Optional[float] = Field(None, description="Updated speed in km/h", ge=0.0)


class BridgeStatusChangedEvent(TwinEvent):
    """
    Emitted when a bridge status changes (e.g. BLOCKED, RESTRICTED).
    Can cause a causal cascading update to its associated road segment.
    """
    event_type: str = Field(default="BRIDGE_STATUS_CHANGED")
    bridge_id: str = Field(..., description="Target bridge identifier")
    previous_status: Optional[BridgeStatus] = Field(None, description="Previous bridge status")
    new_status: BridgeStatus = Field(..., description="New bridge status")
    propagate_to_road: bool = Field(default=True, description="Whether to propagate closure/restriction to associated road")
