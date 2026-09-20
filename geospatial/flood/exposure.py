"""
NEXUS Flood Simulation - Exposure Engine.
Evaluates spatial intersection and exposure of infrastructure and communities
to simulated flood extents.
"""

from typing import List, Optional

from pydantic import BaseModel, Field
from shapely.geometry.base import BaseGeometry

from digital_twin.entities import (
    RoadEntity,
)
from geospatial.flood.extent import SimulatedFloodExtent
from geospatial.spatial_analysis.distance import geometry_length_meters
from geospatial.spatial_analysis.predicates import intersection_geometry, intersects


class RoadExposure(BaseModel):
    """Exposure metrics for an affected road segment."""
    road_id: str
    affected: bool
    submerged_length_meters: float = Field(default=0.0, ge=0.0)
    estimated_depth_m: Optional[float] = None
    closure_recommended: bool = False
    closure_reason: Optional[str] = None


class FacilityExposure(BaseModel):
    """Exposure metrics for an affected point facility (Hospital, Shelter, Bridge)."""
    facility_id: str
    facility_type: str  # 'HOSPITAL', 'SHELTER', 'BRIDGE'
    name: Optional[str] = None
    affected: bool
    estimated_depth_m: Optional[float] = None
    status: Optional[str] = None


class IncidentExposure(BaseModel):
    """Exposure metrics for an existing incident."""
    incident_id: str
    affected: bool
    estimated_depth_m: Optional[float] = None
    severity: Optional[str] = None


class PopulationExposure(BaseModel):
    """Exposure metrics for a population zone/census block."""
    population_id: str
    affected: bool
    exposed_population_count: int = Field(default=0, ge=0)


class VulnerabilityExposure(BaseModel):
    """Exposure metrics for a vulnerable group cluster."""
    vulnerable_group_id: str
    category: str
    affected: bool
    affected_count: int = Field(default=0, ge=0)


class ScenarioExposureResult(BaseModel):
    """
    Consolidated exposure analysis output for a simulated flood extent.
    """
    scenario_id: str
    flood_zone_id: str
    mode: str = "SIMULATION"
    total_flooded_area_m2: float
    affected_roads: List[RoadExposure] = Field(default_factory=list)
    affected_bridges: List[FacilityExposure] = Field(default_factory=list)
    affected_hospitals: List[FacilityExposure] = Field(default_factory=list)
    affected_shelters: List[FacilityExposure] = Field(default_factory=list)
    affected_incidents: List[IncidentExposure] = Field(default_factory=list)
    affected_populations: List[PopulationExposure] = Field(default_factory=list)
    affected_vulnerable_groups: List[VulnerabilityExposure] = Field(default_factory=list)

    @property
    def total_roads_affected(self) -> int:
        return sum(1 for r in self.affected_roads if r.affected)

    @property
    def total_facilities_affected(self) -> int:
        return (
            sum(1 for h in self.affected_hospitals if h.affected)
            + sum(1 for s in self.affected_shelters if s.affected)
            + sum(1 for b in self.affected_bridges if b.affected)
        )


def evaluate_road_exposure(
    road: RoadEntity,
    road_geom: BaseGeometry,
    flood_extent: SimulatedFloodExtent,
    closure_threshold_m: Optional[float] = None,
    auto_close: bool = False,
) -> RoadExposure:
    """
    Evaluates whether a road segment is submerged by the flood extent.
    Enforces the explicit rule: intersection does NOT automatically mark road as BLOCKED
    unless closure_threshold_m is met and auto_close is True.
    """
    flood_geom = flood_extent.to_shapely()
    if not intersects(road_geom, flood_geom):
        return RoadExposure(road_id=road.road_id, affected=False)

    clipped = intersection_geometry(road_geom, flood_geom)
    submerged_len = geometry_length_meters(clipped) if (clipped and not clipped.is_empty) else 0.0

    depth = flood_extent.maximum_depth_m
    should_close = False
    closure_reason = None

    if auto_close and closure_threshold_m is not None and depth is not None:
        if depth >= closure_threshold_m:
            should_close = True
            closure_reason = (
                f"Flood water depth ({depth:.2f}m) exceeds vehicle safety threshold ({closure_threshold_m:.2f}m)"
            )

    return RoadExposure(
        road_id=road.road_id,
        affected=True,
        submerged_length_meters=submerged_len,
        estimated_depth_m=depth,
        closure_recommended=should_close,
        closure_reason=closure_reason,
    )


def evaluate_point_facility_exposure(
    facility_id: str,
    facility_type: str,
    point_geom: BaseGeometry,
    flood_extent: SimulatedFloodExtent,
    name: Optional[str] = None,
) -> FacilityExposure:
    """Evaluates whether a point facility intersects the simulated flood polygon."""
    flood_geom = flood_extent.to_shapely()
    affected = intersects(point_geom, flood_geom)
    depth = flood_extent.maximum_depth_m if affected else None

    return FacilityExposure(
        facility_id=facility_id,
        facility_type=facility_type,
        name=name,
        affected=affected,
        estimated_depth_m=depth,
    )
