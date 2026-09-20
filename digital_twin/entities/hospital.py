"""
NEXUS Digital Twin - Hospital Entity.
Operational capacity and status of healthcare facilities.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator

from services.api.app.schemas.hospital import HospitalStatus


class HospitalEntity(BaseModel):
    """
    Operational representation of a hospital facility.
    Tracks bed capacity, ICU availability, and operational status.
    """
    hospital_id: str = Field(..., description="Unique hospital identifier (e.g. 'H-001')")
    name: str = Field(..., description="Hospital facility name")
    capacity: int = Field(..., description="Total bed capacity", ge=0)
    available_capacity: int = Field(..., description="Currently available beds", ge=0)
    emergency_available: bool = Field(default=True, description="Emergency ward operational")
    icu_available: int = Field(default=0, description="Available ICU beds", ge=0)
    accessibility: str = Field(default="OPEN", description="Facility access status")
    status: HospitalStatus = Field(default=HospitalStatus.OPERATIONAL, description="Operational status")
    location: Optional[Dict[str, Any]] = Field(None, description="Spatial coordinates or GeoJSON geometry")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of last update (UTC)")
    source: str = Field(default="SYSTEM", description="Source of update")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

    @model_validator(mode="after")
    def validate_capacity_bounds(self) -> "HospitalEntity":
        if self.available_capacity > self.capacity:
            raise ValueError(
                f"available_capacity ({self.available_capacity}) cannot exceed total capacity ({self.capacity})"
            )
        return self

    model_config = {
        "frozen": False,
        "validate_assignment": True,
    }
