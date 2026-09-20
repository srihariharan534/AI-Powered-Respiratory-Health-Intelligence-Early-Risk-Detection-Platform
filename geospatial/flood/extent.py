"""
NEXUS Flood Simulation - Extent Model.
Standardized representation of simulated flood extent polygons and metrics.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry

from geospatial.flood.scenario import SimulationMode
from geospatial.flood.thresholds import DEFAULT_THRESHOLDS, FloodSeverity, classify_flood_depth
from geospatial.spatial_analysis.distance import polygon_area_sq_meters
from geospatial.spatial_analysis.validation import validate_geometry


class SimulatedFloodExtent(BaseModel):
    """
    Resulting spatial flood extent generated from a FloodScenario simulation.
    """
    flood_zone_id: str = Field(..., description="Unique flood zone identifier (e.g. 'FZ-SIM-001')")
    scenario_id: str = Field(..., description="Associated scenario identifier")
    mode: SimulationMode = Field(default=SimulationMode.SIMULATION, description="Always SIMULATION")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON polygon or MultiPolygon geometry (EPSG:4326)")
    severity: FloodSeverity = Field(..., description="Classified flood severity")
    maximum_depth_m: Optional[float] = Field(None, ge=0.0, description="Maximum water depth in meters")
    mean_depth_m: Optional[float] = Field(None, ge=0.0, description="Mean water depth in meters")
    area_sq_meters: float = Field(..., ge=0.0, description="Total inundated surface area in square meters")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Simulation timestamp (UTC)")
    source: str = Field(default="NEXUS_SIMULATOR", description="Simulation engine source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata")

    @classmethod
    def from_shapely(
        cls,
        flood_zone_id: str,
        scenario_id: str,
        geometry: BaseGeometry,
        max_depth_m: Optional[float] = None,
        mean_depth_m: Optional[float] = None,
        mode: SimulationMode = SimulationMode.SIMULATION,
        source: str = "NEXUS_SIMULATOR",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "SimulatedFloodExtent":
        """Construct a validated SimulatedFloodExtent from a Shapely geometry."""
        if geometry.is_empty:
            return cls(
                flood_zone_id=flood_zone_id,
                scenario_id=scenario_id,
                mode=mode,
                geometry={"type": "Polygon", "coordinates": []},
                severity=FloodSeverity.LOW,
                maximum_depth_m=0.0,
                mean_depth_m=0.0,
                area_sq_meters=0.0,
                source=source,
                metadata=metadata or {},
            )

        validate_geometry(geometry)
        area_m2 = polygon_area_sq_meters(geometry)

        # Severity determined by max_depth_m or fallback to MODERATE if depth unavailable
        severity = (
            classify_flood_depth(max_depth_m, DEFAULT_THRESHOLDS)
            if max_depth_m is not None
            else FloodSeverity.MODERATE
        )

        return cls(
            flood_zone_id=flood_zone_id,
            scenario_id=scenario_id,
            mode=mode,
            geometry=mapping(geometry),
            severity=severity,
            maximum_depth_m=max_depth_m,
            mean_depth_m=mean_depth_m,
            area_sq_meters=area_m2,
            source=source,
            metadata=metadata or {},
        )

    def to_shapely(self) -> BaseGeometry:
        """Convert GeoJSON geometry to Shapely geometry."""
        return shape(self.geometry)

    model_config = {
        "frozen": True,
    }
