"""
Dynamic Operational Road State Models for NEXUS Emergency Routing (Phase 08).
Defines structures for non-destructive operational overrides on the base road graph.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from services.api.app.schemas.road import Accessibility, RoadStatus


class OverrideSource(str, Enum):
    """Origin of a dynamic state change."""
    FIELD_REPORT = "FIELD_REPORT"
    COMMAND_CENTER = "COMMAND_CENTER"
    SIMULATION = "SIMULATION"
    INFRASTRUCTURE_UPDATE = "INFRASTRUCTURE_UPDATE"
    AUTHORIZED_OPERATOR = "AUTHORIZED_OPERATOR"
    TEST_FIXTURE = "TEST_FIXTURE"


class RoadStateOverride(BaseModel):
    """
    Dynamic operational state override applied to a road or bridge.
    Does NOT mutate the immutable underlying OSM road graph.
    """
    model_config = ConfigDict(extra="forbid")
    road_id: str
    status: RoadStatus
    accessibility: Optional[Accessibility] = None
    speed_limit_kmh: Optional[float] = Field(default=None, ge=0.0)
    reason: str = Field(..., min_length=1)
    source: OverrideSource = OverrideSource.SIMULATION
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    bridge_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RoadStateChangedEvent(BaseModel):
    """
    Internal event recorded whenever a road or bridge state is updated or cleared.
    """
    model_config = ConfigDict(extra="forbid")
    event_id: str
    road_id: str
    previous_status: Optional[RoadStatus] = None
    new_status: Optional[RoadStatus] = None  # None if cleared
    reason: str
    source: OverrideSource
    state_version: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
