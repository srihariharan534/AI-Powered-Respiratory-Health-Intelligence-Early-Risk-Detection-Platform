"""
Canonical Incident Pydantic Contract.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IncidentEventType(str, Enum):
    FLOOD_INUNDATION = "FLOOD_INUNDATION"
    ROAD_BLOCKED = "ROAD_BLOCKED"
    BRIDGE_FAILURE = "BRIDGE_FAILURE"
    EMBANKMENT_BREACH = "EMBANKMENT_BREACH"
    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY"
    TRAPPED_PERSONS = "TRAPPED_PERSONS"
    SHELTER_NEEDED = "SHELTER_NEEDED"
    RESOURCE_REQUEST = "RESOURCE_REQUEST"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class IncidentSource(str, Enum):
    FIELD_OFFICER = "field_officer"
    SMS = "sms"
    MANUAL_ENTRY = "manual_entry"
    SIMULATOR = "simulator"
    OSM = "osm"
    HISTORICAL_FLOOD_DATASET = "historical_flood_dataset"
    SYNTHETIC_DEMO = "synthetic_demo"


class PointLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["Point"] = "Point"
    coordinates: list[float] = Field(..., min_length=2, max_length=2)

    @property
    def longitude(self) -> float:
        return self.coordinates[0]

    @property
    def latitude(self) -> float:
        return self.coordinates[1]

    @model_validator(mode="after")
    def validate_coordinate_ranges(self) -> "PointLocation":
        lon, lat = self.coordinates[0], self.coordinates[1]
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude {lon} must be between -180 and 180 degrees.")
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude {lat} must be between -90 and 90 degrees.")
        return self


class IncidentEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    water_depth_cm: float | None = Field(default=None, ge=0.0)
    trapped_count: int | None = Field(default=None, ge=0)
    notes: str | None = None


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    incident_id: str = Field(..., min_length=3)
    event_type: IncidentEventType
    severity: IncidentSeverity
    status: IncidentStatus
    priority: int = Field(..., ge=1, le=5)
    location: PointLocation
    description: str
    reported_at: datetime
    reported_by: str
    source: IncidentSource
    evidence: IncidentEvidence | None = None
