"""
NEXUS Digital Twin - Bridge Entity.
Operational state of bridges in the emergency environment.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BridgeStatus(str, Enum):
    OPEN = "OPEN"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    COLLAPSED = "COLLAPSED"
    SUBMERGED = "SUBMERGED"
    CLOSED = "CLOSED"


class BridgeEntity(BaseModel):
    """
    Operational representation of a bridge.
    A bridge status change (e.g. BLOCKED/COLLAPSED) propagates to associated roads.
    """
    bridge_id: str = Field(..., description="Unique bridge identifier (e.g. 'B-001')")
    name: Optional[str] = Field(None, description="Bridge name or description")
    road_id: Optional[str] = Field(None, description="Primary associated road segment ID")
    status: BridgeStatus = Field(default=BridgeStatus.OPEN, description="Operational bridge status")
    clearance_m: Optional[float] = Field(None, description="Vertical clearance in meters", ge=0.0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of last update (UTC)")
    source: str = Field(default="SYSTEM", description="Source of update (e.g. FIELD_REPORT, SIMULATION)")
    reason: Optional[str] = Field(None, description="Reason for bridge status change")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata")

    model_config = {
        "frozen": False,
        "validate_assignment": True,
    }
