"""
Canonical Road Pydantic Contract.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RoadType(str, Enum):
    MOTORWAY = "motorway"
    TRUNK = "trunk"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    RESIDENTIAL = "residential"
    BRIDGE = "bridge"
    CULVERT = "culvert"


class RoadStatus(str, Enum):
    OPEN = "OPEN"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class Accessibility(str, Enum):
    ALL_VEHICLES = "ALL_VEHICLES"
    EMERGENCY_ONLY = "EMERGENCY_ONLY"
    HIGH_CLEARANCE_ONLY = "HIGH_CLEARANCE_ONLY"
    IMPASSABLE = "IMPASSABLE"


class RoadSource(str, Enum):
    OSM = "osm"
    FIELD_OFFICER = "field_officer"
    SIMULATOR = "simulator"
    SYNTHETIC_DEMO = "synthetic_demo"


class LineGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["LineString", "MultiLineString"] = "LineString"
    coordinates: list[list[float]] = Field(..., min_length=2)


class Road(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    road_id: str = Field(..., min_length=3)
    name: str
    road_type: RoadType
    status: RoadStatus
    accessibility: Accessibility
    geometry: LineGeometry
    speed_limit_kmh: float | None = Field(default=None, ge=0.0, le=150.0)
    capacity_vehicles_per_hour: int | None = Field(default=None, ge=0)
    flood_depth_cm: float | None = Field(default=None, ge=0.0)
    last_updated: datetime
    source: RoadSource
