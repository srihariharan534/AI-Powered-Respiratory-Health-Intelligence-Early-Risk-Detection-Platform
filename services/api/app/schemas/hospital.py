"""
Canonical Hospital Pydantic Contract.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.api.app.schemas.incident import PointLocation
from services.api.app.schemas.road import Accessibility


class HospitalStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    OVERLOADED = "OVERLOADED"
    EVACUATING = "EVACUATING"
    CLOSED = "CLOSED"


class HospitalSource(str, Enum):
    OSM = "osm"
    HEALTH_REGISTRY = "health_registry"
    MANUAL_ENTRY = "manual_entry"
    SIMULATOR = "simulator"
    SYNTHETIC_DEMO = "synthetic_demo"


class Hospital(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    hospital_id: str = Field(..., min_length=3)
    name: str
    location: PointLocation
    status: HospitalStatus
    accessibility: Accessibility = Accessibility.ALL_VEHICLES
    capacity: int = Field(..., ge=0)
    available_capacity: int = Field(..., ge=0)
    emergency_available: bool = True
    icu_available: int = Field(default=0, ge=0)
    last_updated: datetime
    source: HospitalSource

    @model_validator(mode="after")
    def validate_capacity_bounds(self) -> "Hospital":
        if self.available_capacity > self.capacity:
            msg = (
                f"available_capacity ({self.available_capacity}) "
                f"cannot exceed total capacity ({self.capacity})"
            )
            raise ValueError(msg)
        return self
