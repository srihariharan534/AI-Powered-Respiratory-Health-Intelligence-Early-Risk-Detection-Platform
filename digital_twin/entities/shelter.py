"""
NEXUS Digital Twin - Shelter Entity.
Operational capacity and status of emergency evacuation shelters.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator

from services.api.app.schemas.shelter import ShelterStatus


class ShelterEntity(BaseModel):
    """
    Operational representation of an emergency shelter.
    Tracks population capacity, availability, and access status.
    """
    shelter_id: str = Field(..., description="Unique shelter identifier (e.g. 'S-001')")
    name: str = Field(..., description="Shelter facility name")
    capacity: int = Field(..., description="Maximum shelter capacity (people)", ge=0)
    available_capacity: int = Field(..., description="Available capacity (people)", ge=0)
    accessibility: str = Field(default="OPEN", description="Accessibility status")
    status: ShelterStatus = Field(default=ShelterStatus.OPEN, description="Operational status")
    location: Optional[Dict[str, Any]] = Field(None, description="Spatial coordinates or GeoJSON point")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of last update (UTC)")
    source: str = Field(default="SYSTEM", description="Source of update")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

    @model_validator(mode="after")
    def validate_capacity_bounds(self) -> "ShelterEntity":
        if self.available_capacity > self.capacity:
            raise ValueError(
                f"available_capacity ({self.available_capacity}) cannot exceed total capacity ({self.capacity})"
            )
        return self

    model_config = {
        "frozen": False,
        "validate_assignment": True,
    }
