"""
NEXUS Digital Twin - Facility Status Changed Event.
Authoritative operational status adjustments for hospitals and shelters.
"""

from typing import Literal

from pydantic import Field

from digital_twin.events.base import TwinEvent


class FacilityStatusChangedEvent(TwinEvent):
    """
    Emitted when an operational facility status transitions
    (e.g., Hospital: OPERATIONAL -> OVERLOADED -> EVACUATING -> CLOSED,
     Shelter: OPEN -> AT_CAPACITY -> STANDBY -> CLOSED).
    """
    event_type: str = Field(default="FACILITY_STATUS_CHANGED")
    facility_type: Literal["HOSPITAL", "SHELTER"] = Field(
        ..., description="Type of facility: 'HOSPITAL' or 'SHELTER'"
    )
    facility_id: str = Field(
        ..., description="Target facility identifier (e.g. 'H-001' or 'S-001')"
    )
    previous_status: str = Field(..., description="Previous operational status string")
    new_status: str = Field(..., description="Target operational status string")
