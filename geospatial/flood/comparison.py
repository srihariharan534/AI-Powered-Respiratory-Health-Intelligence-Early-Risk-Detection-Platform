"""
NEXUS Flood Simulation - Scenario Comparison.
Compares two simulation runs (e.g. Baseline vs Scenario +1m) to determine
marginal delta in flood extent and newly exposed infrastructure.
"""

from typing import List, Set

from pydantic import BaseModel, Field

from geospatial.flood.exposure import ScenarioExposureResult
from geospatial.flood.extent import SimulatedFloodExtent
from geospatial.spatial_analysis.distance import polygon_area_sq_meters


class ScenarioComparisonResult(BaseModel):
    """
    Comparison output between baseline and simulated flood scenario.
    """
    baseline_scenario_id: str
    scenario_id: str
    newly_flooded_area_sq_meters: float = Field(default=0.0, ge=0.0)
    newly_affected_roads: List[str] = Field(default_factory=list, description="IDs of newly affected roads")
    newly_affected_bridges: List[str] = Field(default_factory=list, description="IDs of newly affected bridges")
    newly_affected_hospitals: List[str] = Field(default_factory=list, description="IDs of newly affected hospitals")
    newly_affected_shelters: List[str] = Field(default_factory=list, description="IDs of newly affected shelters")
    newly_affected_incidents: List[str] = Field(default_factory=list, description="IDs of newly affected incidents")


def compare_scenarios(
    baseline_extent: SimulatedFloodExtent,
    baseline_exposure: ScenarioExposureResult,
    scenario_extent: SimulatedFloodExtent,
    scenario_exposure: ScenarioExposureResult,
) -> ScenarioComparisonResult:
    """
    Computes spatial differential and newly affected infrastructure between two scenarios.
    """
    base_geom = baseline_extent.to_shapely()
    scen_geom = scenario_extent.to_shapely()

    # Newly flooded area = Area(Scenario - Baseline)
    diff_geom = scen_geom.difference(base_geom)
    new_area = polygon_area_sq_meters(diff_geom) if (diff_geom and not diff_geom.is_empty) else 0.0

    # Road differences
    base_roads: Set[str] = {r.road_id for r in baseline_exposure.affected_roads if r.affected}
    scen_roads: Set[str] = {r.road_id for r in scenario_exposure.affected_roads if r.affected}
    new_roads = sorted(list(scen_roads - base_roads))

    # Facility differences
    base_bridges: Set[str] = {b.facility_id for b in baseline_exposure.affected_bridges if b.affected}
    scen_bridges: Set[str] = {b.facility_id for b in scenario_exposure.affected_bridges if b.affected}
    new_bridges = sorted(list(scen_bridges - base_bridges))

    base_hosps: Set[str] = {h.facility_id for h in baseline_exposure.affected_hospitals if h.affected}
    scen_hosps: Set[str] = {h.facility_id for h in scenario_exposure.affected_hospitals if h.affected}
    new_hosps = sorted(list(scen_hosps - base_hosps))

    base_shelters: Set[str] = {s.facility_id for s in baseline_exposure.affected_shelters if s.affected}
    scen_shelters: Set[str] = {s.facility_id for s in scenario_exposure.affected_shelters if s.affected}
    new_shelters = sorted(list(scen_shelters - base_shelters))

    base_incidents: Set[str] = {i.incident_id for i in baseline_exposure.affected_incidents if i.affected}
    scen_incidents: Set[str] = {i.incident_id for i in scenario_exposure.affected_incidents if i.affected}
    new_incidents = sorted(list(scen_incidents - base_incidents))

    return ScenarioComparisonResult(
        baseline_scenario_id=baseline_extent.scenario_id,
        scenario_id=scenario_extent.scenario_id,
        newly_flooded_area_sq_meters=new_area,
        newly_affected_roads=new_roads,
        newly_affected_bridges=new_bridges,
        newly_affected_hospitals=new_hosps,
        newly_affected_shelters=new_shelters,
        newly_affected_incidents=new_incidents,
    )
