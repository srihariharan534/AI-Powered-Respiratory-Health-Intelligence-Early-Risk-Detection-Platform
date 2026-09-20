"""
Canonical Shelter Pydantic Contract.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.api.app.schemas.incident import PointLocation
from services.api.app.schemas.road import Accessibility


class ShelterStatus(str, Enum):
    OPEN = "OPEN"
    AT_CAPACITY = "AT_CAPACITY"
    STANDBY = "STANDBY"
    CLOSED = "CLOSED"


class ShelterSource(str, Enum):
    OSM = "osm"
    DISTRICT_REGISTRY = "district_registry"
    MANUAL_ENTRY = "manual_entry"
    SIMULATOR = "simulator"
    SYNTHETIC_DEMO = "synthetic_demo"


class Shelter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    shelter_id: str = Field(..., min_length=3)
    name: str
    location: PointLocation
    status: ShelterStatus
    accessibility: Accessibility = Accessibility.ALL_VEHICLES
    capacity: int = Field(..., ge=0)
    available_capacity: int = Field(..., ge=0)
    has_power_backup: bool = False
    has_potable_water: bool = True
    last_updated: datetime
    source: ShelterSource

    @model_validator(mode="after")
    def validate_capacity_bounds(self) -> "Shelter":
        if self.available_capacity > self.capacity:
            msg = (
                f"available_capacity ({self.available_capacity}) "
                f"cannot exceed total capacity ({self.capacity})"
            )
            raise ValueError(msg)
        return self
