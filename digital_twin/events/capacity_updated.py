"""
NEXUS Digital Twin - Capacity Updated Event.
Operational capacity adjustments for hospitals, shelters, and emergency resources.
"""

from typing import Optional

from pydantic import Field, model_validator

from digital_twin.events.base import TwinEvent


class CapacityUpdatedEvent(TwinEvent):
    """
    Emitted when facility capacity or available capacity changes (e.g. hospital beds, shelter spots).
    Validates: 0 <= available_capacity <= capacity.
    """
    event_type: str = Field(default="CAPACITY_UPDATED")
    facility_type: str = Field(..., description="Type of facility: 'HOSPITAL' or 'SHELTER'")
    facility_id: str = Field(..., description="Target facility identifier (e.g. 'H-001' or 'S-001')")
    capacity: int = Field(..., description="Total maximum capacity", ge=0)
    available_capacity: int = Field(..., description="Remaining available capacity", ge=0)
    icu_available: Optional[int] = Field(None, description="Available ICU beds (for hospitals only)", ge=0)
    accessibility: Optional[str] = Field(None, description="Updated access status (e.g. OPEN, RESTRICTED)")

    @model_validator(mode="after")
    def validate_capacity_bounds(self) -> "CapacityUpdatedEvent":
        if self.available_capacity > self.capacity:
            raise ValueError(
                f"available_capacity ({self.available_capacity}) cannot exceed total capacity ({self.capacity})"
            )
        return self
