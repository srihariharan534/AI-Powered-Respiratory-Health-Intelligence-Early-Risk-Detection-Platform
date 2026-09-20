"""
NEXUS Flood Simulation - Scenario Models.
Defines flood scenario parameters, simulation modes, and environmental inputs.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from geospatial.spatial_analysis.validation import validate_geometry


class SimulationMode(str, Enum):
    """
    Simulation mode indicator.
    CRITICAL: Output must never be presented as LIVE or PREDICTED.
    """
    SIMULATION = "SIMULATION"
    TEST_FIXTURE = "TEST_FIXTURE"


class ScenarioType(str, Enum):
    """Type of flood scenario specification."""
    WATER_LEVEL = "WATER_LEVEL"           # Absolute water level (meters above datum)
    DEPTH_INCREMENT = "DEPTH_INCREMENT"   # Uniform water level increment (+X meters)
    EXPLICIT_POLYGON = "EXPLICIT_POLYGON" # Direct spatial flood extent polygon


class FloodScenario(BaseModel):
    """
    Formal Flood Simulation Scenario definition.
    Encapsulates environmental assumptions, water levels, or explicit polygons.
    """
    scenario_id: str = Field(..., min_length=3, description="Unique, deterministic scenario identifier")
    name: str = Field(..., description="Human-readable scenario description")
    mode: SimulationMode = Field(default=SimulationMode.SIMULATION, description="Always SIMULATION or TEST_FIXTURE")
    scenario_type: ScenarioType = Field(..., description="Mechanism used to evaluate inundation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC scenario creation time")

    # Parameters for WATER_LEVEL and DEPTH_INCREMENT
    baseline_water_level_m: Optional[float] = Field(None, description="Baseline environmental water level in meters")
    water_level_m: Optional[float] = Field(None, description="Scenario absolute water level in meters")
    depth_increment_m: Optional[float] = Field(None, ge=0.0, description="Positive depth increment (e.g. +1.0m)")

    # Parameters for EXPLICIT_POLYGON
    flood_polygon: Optional[Dict[str, Any]] = Field(None, description="GeoJSON polygon or MultiPolygon geometry")
    explicit_depth_m: Optional[float] = Field(None, ge=0.0, description="Uniform flood depth for explicit polygon mode")

    # Configurable infrastructure impact rules
    road_closure_depth_threshold_m: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        description="Depth above which roads are marked BLOCKED in operational sync (default: 0.3m)",
    )
    auto_close_roads: bool = Field(
        default=False,
        description="If True, roads exceeding road_closure_depth_threshold_m are flagged for closure; default False",
    )

    source: str = Field(default="NEXUS_SCENARIO_SIMULATOR", description="Source or author of the scenario")
    description: Optional[str] = Field(None, description="Detailed operational rationale or hazard narrative")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary scenario parameters")

    @model_validator(mode="after")
    def validate_scenario_parameters(self) -> "FloodScenario":
        if self.scenario_type == ScenarioType.WATER_LEVEL:
            if self.water_level_m is None:
                raise ValueError("water_level_m is required for WATER_LEVEL scenario")
        elif self.scenario_type == ScenarioType.DEPTH_INCREMENT:
            if self.depth_increment_m is None:
                raise ValueError("depth_increment_m is required for DEPTH_INCREMENT scenario")
            if self.baseline_water_level_m is None:
                raise ValueError("baseline_water_level_m is required when applying depth_increment_m")
        elif self.scenario_type == ScenarioType.EXPLICIT_POLYGON:
            if self.flood_polygon is None:
                raise ValueError("flood_polygon is required for EXPLICIT_POLYGON scenario")
            try:
                geom: BaseGeometry = shape(self.flood_polygon)
                if geom.is_empty:
                    raise ValueError("flood_polygon cannot be empty")
                validate_geometry(geom)
            except Exception as e:
                raise ValueError(f"Invalid flood_polygon geometry: {e}") from e

        return self

    def get_effective_water_level(self) -> Optional[float]:
        """Calculates effective water level in meters, if applicable."""
        if self.scenario_type == ScenarioType.WATER_LEVEL:
            return self.water_level_m
        elif self.scenario_type == ScenarioType.DEPTH_INCREMENT:
            assert self.baseline_water_level_m is not None
            assert self.depth_increment_m is not None
            return self.baseline_water_level_m + self.depth_increment_m
        return None

    model_config = {
        "frozen": True,
    }
