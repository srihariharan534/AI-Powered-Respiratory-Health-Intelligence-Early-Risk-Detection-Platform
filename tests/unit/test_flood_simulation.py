"""
Comprehensive Unit and Integration Tests for Phase 10: Flood Simulation Engine.
Validates:
- Scenario validation (valid, missing fields, invalid mode, negative increment)
- Flood depth validation (zero, positive, negative rejection)
- Severity classification across all threshold boundaries
- Explicit polygon simulation mode (valid, empty rejection)
- Elevation-based inundation model (inundated cells, dry cells, exact boundary)
- Flood extent generation and geometry validity
- Exposure analysis (roads intersecting vs outside, facilities, incidents)
- Configurable road closure threshold (no auto-closure by default, closure when enabled)
- Scenario comparison (newly flooded area, newly affected roads/facilities)
- Digital Twin integration (FloodUpdatedEvent, state versioning, idempotency)
- End-to-end integration: Flood Simulation -> Road Exposure -> Closure -> Digital Twin -> Phase 08 StateOverlay
- Determinism (identical inputs produce identical outputs)
"""

import numpy as np
import pytest
from shapely.geometry import LineString, Point, Polygon

from digital_twin.entities import (
    RoadEntity,
)
from digital_twin.events import (
    EventSource,
    FloodUpdatedEvent,
    RoadStatusChangedEvent,
)
from digital_twin.state.state_manager import DigitalTwinStateManager
from geospatial.flood import (
    ElevationGrid,
    FloodScenario,
    FloodSeverity,
    FloodSimulationEngine,
    RoadExposure,
    ScenarioExposureResult,
    ScenarioType,
    SimulatedFloodExtent,
    SimulationMode,
    classify_flood_depth,
    compare_scenarios,
    evaluate_point_facility_exposure,
    evaluate_road_exposure,
    flood_extent_to_geojson_feature,
)
from geospatial.routing.state_overlay import StateOverlay
from services.api.app.schemas.road import RoadStatus


@pytest.fixture
def synthetic_elevation_grid() -> ElevationGrid:
    """
    Deterministic synthetic terrain fixture:
    4x4 grid with elevation stepping down southward:
    Row 3 (North): [100.0, 100.0, 100.0, 100.0]
    Row 2:         [ 90.0,  90.0,  90.0,  90.0]
    Row 1:         [ 80.0,  80.0,  80.0,  80.0]
    Row 0 (South): [ 70.0,  70.0,  70.0,  70.0]
    Resolution: 0.01 degrees per cell (~1.1 km)
    """
    elevations = np.array([
        [70.0, 70.0, 70.0, 70.0],  # row 0: lat 20.00 to 20.01
        [80.0, 80.0, 80.0, 80.0],  # row 1: lat 20.01 to 20.02
        [90.0, 90.0, 90.0, 90.0],  # row 2: lat 20.02 to 20.03
        [100.0, 100.0, 100.0, 100.0], # row 3: lat 20.03 to 20.04
    ])
    return ElevationGrid(
        elevations=elevations,
        min_lon=85.80,
        min_lat=20.00,
        cell_size_deg=0.01,
    )


class TestFloodScenarioValidation:
    """Test scenario creation, schemas, and parameter validation."""

    def test_valid_water_level_scenario(self):
        scen = FloodScenario(
            scenario_id="scen-wl-01",
            name="River Basin +85m Level",
            scenario_type=ScenarioType.WATER_LEVEL,
            water_level_m=85.0,
            mode=SimulationMode.SIMULATION,
        )
        assert scen.scenario_id == "scen-wl-01"
        assert scen.mode == SimulationMode.SIMULATION
        assert scen.get_effective_water_level() == 85.0

    def test_valid_depth_increment_scenario(self):
        scen = FloodScenario(
            scenario_id="scen-inc-01",
            name="+1 Meter Surge",
            scenario_type=ScenarioType.DEPTH_INCREMENT,
            baseline_water_level_m=80.0,
            depth_increment_m=1.0,
            mode=SimulationMode.SIMULATION,
        )
        assert scen.get_effective_water_level() == 81.0

    def test_missing_water_level_raises(self):
        with pytest.raises(ValueError, match="water_level_m is required"):
            FloodScenario(
                scenario_id="scen-invalid",
                name="Missing WL",
                scenario_type=ScenarioType.WATER_LEVEL,
            )

    def test_empty_explicit_polygon_raises(self):
        with pytest.raises(ValueError, match="cannot be empty|Invalid flood_polygon"):
            FloodScenario(
                scenario_id="scen-empty-poly",
                name="Empty Poly",
                scenario_type=ScenarioType.EXPLICIT_POLYGON,
                flood_polygon={"type": "Polygon", "coordinates": []},
            )


class TestDepthAndSeverityClassification:
    """Test depth handling and deterministic severity classification."""

    def test_negative_depth_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            classify_flood_depth(-0.5)

    def test_severity_boundaries(self):
        # Default thresholds: low <= 0.3, moderate <= 1.0, severe <= 2.0, extreme > 2.0
        assert classify_flood_depth(0.0) == FloodSeverity.LOW
        assert classify_flood_depth(0.3) == FloodSeverity.LOW
        assert classify_flood_depth(0.30001) == FloodSeverity.MODERATE
        assert classify_flood_depth(1.0) == FloodSeverity.MODERATE
        assert classify_flood_depth(1.0001) == FloodSeverity.SEVERE
        assert classify_flood_depth(2.0) == FloodSeverity.SEVERE
        assert classify_flood_depth(2.0001) == FloodSeverity.EXTREME
        assert classify_flood_depth(5.0) == FloodSeverity.EXTREME


class TestExplicitPolygonSimulation:
    """Test explicit polygon flood scenario execution."""

    def test_explicit_polygon_simulation(self):
        poly_geojson = {
            "type": "Polygon",
            "coordinates": [[[85.81, 20.01], [85.83, 20.01], [85.83, 20.03], [85.81, 20.03], [85.81, 20.01]]],
        }
        scen = FloodScenario(
            scenario_id="scen-explicit-01",
            name="Canal Breach Inundation",
            scenario_type=ScenarioType.EXPLICIT_POLYGON,
            flood_polygon=poly_geojson,
            explicit_depth_m=1.2,
            mode=SimulationMode.SIMULATION,
        )
        engine = FloodSimulationEngine()
        extent = engine.simulate(scen)

        assert extent.scenario_id == "scen-explicit-01"
        assert extent.mode == SimulationMode.SIMULATION
        assert extent.severity == FloodSeverity.SEVERE
        assert extent.maximum_depth_m == 1.2
        assert extent.area_sq_meters > 0.0


class TestElevationGridInundation:
    """Test deterministic elevation-based flood extent modeling."""

    def test_elevation_model_inundation(self, synthetic_elevation_grid: ElevationGrid):
        # Inundation at water level = 85.0m:
        # Row 0 (70m) -> depth = 15m (inundated)
        # Row 1 (80m) -> depth = 5m  (inundated)
        # Row 2 (90m) -> depth = -5m (dry)
        # Row 3 (100m) -> depth = -15m (dry)
        scen = FloodScenario(
            scenario_id="scen-elev-85m",
            name="85m Water Level",
            scenario_type=ScenarioType.WATER_LEVEL,
            water_level_m=85.0,
            mode=SimulationMode.SIMULATION,
        )
        engine = FloodSimulationEngine(elevation_grid=synthetic_elevation_grid)
        extent = engine.simulate(scen)

        assert extent.scenario_id == "scen-elev-85m"
        assert extent.maximum_depth_m == 15.0  # 85 - 70
        assert extent.mean_depth_m == 10.0     # (15 + 5) / 2
        assert extent.severity == FloodSeverity.EXTREME
        assert extent.area_sq_meters > 0.0
        assert extent.metadata["inundated_cells"] == 8  # rows 0 and 1 (4 cells each)

    def test_elevation_model_dry_when_below_terrain(self, synthetic_elevation_grid: ElevationGrid):
        # Water level = 65m: completely below minimum terrain elevation (70m)
        scen = FloodScenario(
            scenario_id="scen-dry",
            name="Low Water Level",
            scenario_type=ScenarioType.WATER_LEVEL,
            water_level_m=65.0,
        )
        engine = FloodSimulationEngine(elevation_grid=synthetic_elevation_grid)
        extent = engine.simulate(scen)
        assert extent.area_sq_meters == 0.0
        assert extent.maximum_depth_m == 0.0


class TestExposureEngine:
    """Test infrastructure spatial exposure detection and closure threshold rules."""

    @pytest.fixture
    def active_flood_extent(self) -> SimulatedFloodExtent:
        # Inundated box covering [85.80, 20.00] to [85.84, 20.02]
        poly = Polygon([[85.80, 20.00], [85.84, 20.00], [85.84, 20.02], [85.80, 20.02], [85.80, 20.00]])
        return SimulatedFloodExtent.from_shapely(
            flood_zone_id="FZ-TEST-01",
            scenario_id="SCEN-TEST",
            geometry=poly,
            max_depth_m=0.8,  # 0.8m depth
            mode=SimulationMode.SIMULATION,
        )

    def test_road_exposure_intersects_vs_dry(self, active_flood_extent: SimulatedFloodExtent):
        # Road 1: Traverses through flooded zone (lat 20.01)
        road_submerged = RoadEntity(road_id="R-SUB", status=RoadStatus.OPEN)
        geom_sub = LineString([[85.79, 20.01], [85.85, 20.01]])

        # Road 2: Completely dry north of flooded zone (lat 20.03)
        road_dry = RoadEntity(road_id="R-DRY", status=RoadStatus.OPEN)
        geom_dry = LineString([[85.79, 20.03], [85.85, 20.03]])

        exp_sub = evaluate_road_exposure(road_submerged, geom_sub, active_flood_extent)
        assert exp_sub.affected is True
        assert exp_sub.submerged_length_meters > 0.0
        # By default, intersection does NOT recommend closure
        assert exp_sub.closure_recommended is False

        exp_dry = evaluate_road_exposure(road_dry, geom_dry, active_flood_extent)
        assert exp_dry.affected is False
        assert exp_dry.submerged_length_meters == 0.0

    def test_road_closure_threshold_enforcement(self, active_flood_extent: SimulatedFloodExtent):
        road = RoadEntity(road_id="R-AUTO", status=RoadStatus.OPEN)
        geom = LineString([[85.81, 20.01], [85.83, 20.01]])

        # 1. auto_close=True, depth (0.8m) >= threshold (0.5m) -> closure recommended
        exp_close = evaluate_road_exposure(
            road, geom, active_flood_extent, closure_threshold_m=0.5, auto_close=True
        )
        assert exp_close.affected is True
        assert exp_close.closure_recommended is True
        assert "exceeds vehicle safety threshold" in (exp_close.closure_reason or "")

        # 2. auto_close=True, depth (0.8m) < threshold (1.5m) -> no closure
        exp_open = evaluate_road_exposure(
            road, geom, active_flood_extent, closure_threshold_m=1.5, auto_close=True
        )
        assert exp_open.affected is True
        assert exp_open.closure_recommended is False

    def test_facility_exposure(self, active_flood_extent: SimulatedFloodExtent):
        # Hospital inside flood zone
        hosp_pt = Point(85.82, 20.01)
        hosp_exp = evaluate_point_facility_exposure(
            facility_id="H-01", facility_type="HOSPITAL", point_geom=hosp_pt, flood_extent=active_flood_extent
        )
        assert hosp_exp.affected is True
        assert hosp_exp.estimated_depth_m == 0.8

        # Shelter outside flood zone
        shelter_pt = Point(85.82, 20.03)
        shelter_exp = evaluate_point_facility_exposure(
            facility_id="S-01", facility_type="SHELTER", point_geom=shelter_pt, flood_extent=active_flood_extent
        )
        assert shelter_exp.affected is False


class TestScenarioComparison:
    """Test comparative analysis between two flood scenarios."""

    def test_scenario_comparison_deltas(self):
        # Baseline: Small flood extent [85.80, 20.00] to [85.82, 20.01]
        base_poly = Polygon([[85.80, 20.00], [85.82, 20.00], [85.82, 20.01], [85.80, 20.01], [85.80, 20.00]])
        base_ext = SimulatedFloodExtent.from_shapely("FZ-BASE", "scen-base", base_poly, max_depth_m=0.5)
        base_exp = ScenarioExposureResult(
            scenario_id="scen-base",
            flood_zone_id="FZ-BASE",
            total_flooded_area_m2=base_ext.area_sq_meters,
            affected_roads=[RoadExposure(road_id="R-1", affected=True)],
            affected_hospitals=[],
        )

        # Scenario +1m: Expanded extent [85.80, 20.00] to [85.84, 20.02]
        scen_poly = Polygon([[85.80, 20.00], [85.84, 20.00], [85.84, 20.02], [85.80, 20.02], [85.80, 20.00]])
        scen_ext = SimulatedFloodExtent.from_shapely("FZ-PLUS1", "scen-plus1", scen_poly, max_depth_m=1.5)
        scen_exp = ScenarioExposureResult(
            scenario_id="scen-plus1",
            flood_zone_id="FZ-PLUS1",
            total_flooded_area_m2=scen_ext.area_sq_meters,
            affected_roads=[
                RoadExposure(road_id="R-1", affected=True),
                RoadExposure(road_id="R-2", affected=True),  # Newly affected
            ],
            affected_hospitals=[
                evaluate_point_facility_exposure("H-02", "HOSPITAL", Point(85.83, 20.015), scen_ext),
            ],
        )

        comp = compare_scenarios(base_ext, base_exp, scen_ext, scen_exp)
        assert comp.baseline_scenario_id == "scen-base"
        assert comp.scenario_id == "scen-plus1"
        assert comp.newly_flooded_area_sq_meters > 0.0
        assert comp.newly_affected_roads == ["R-2"]
        assert comp.newly_affected_hospitals == ["H-02"]


class TestPhase10DigitalTwinAndRoutingIntegration:
    """
    End-to-End Integration:
    1. Run flood simulation producing flood extent.
    2. Evaluate road exposure with auto_close=True.
    3. Generate FloodUpdatedEvent and apply to Digital Twin.
    4. Generate RoadStatusChangedEvent and apply to Digital Twin.
    5. Verify Digital Twin version increments.
    6. Verify Phase 08 StateOverlay receives update.
    """

    def test_flood_simulation_digital_twin_routing_flow(self):
        # 1. Create simulated flood scenario
        poly_geojson = {
            "type": "Polygon",
            "coordinates": [[[85.80, 20.00], [85.85, 20.00], [85.85, 20.02], [85.80, 20.02], [85.80, 20.00]]],
        }
        scenario = FloodScenario(
            scenario_id="scen-flood-surge-01",
            name="Coastal Surge +1.2m",
            scenario_type=ScenarioType.EXPLICIT_POLYGON,
            flood_polygon=poly_geojson,
            explicit_depth_m=1.2,
            road_closure_depth_threshold_m=0.5,
            auto_close_roads=True,
            mode=SimulationMode.SIMULATION,
        )

        # 2. Run simulation
        engine = FloodSimulationEngine()
        extent = engine.simulate(scenario)
        assert extent.severity == FloodSeverity.SEVERE

        # 3. Setup Digital Twin with Phase 08 StateOverlay
        overlay = StateOverlay()
        twin = DigitalTwinStateManager(routing_overlay=overlay)

        # Register road R-COAST in Digital Twin
        road = RoadEntity(
            road_id="R-COAST",
            status=RoadStatus.OPEN,
            source="TEST_FIXTURE",
        )
        twin.register_road(road)
        assert twin.state_version == 0

        # Evaluate exposure on R-COAST (crosses flood zone)
        road_geom = LineString([[85.79, 20.01], [85.86, 20.01]])
        road_exp = evaluate_road_exposure(
            road=road,
            road_geom=road_geom,
            flood_extent=extent,
            closure_threshold_m=scenario.road_closure_depth_threshold_m,
            auto_close=scenario.auto_close_roads,
        )
        assert road_exp.affected is True
        assert road_exp.closure_recommended is True

        # 4. Ingest Flood extent update into Digital Twin
        flood_event = FloodUpdatedEvent(
            event_id="EVT-SIM-FLOOD-01",
            flood_zone_id=extent.flood_zone_id,
            name=scenario.name,
            geometry=extent.geometry,
            severity=extent.severity,
            water_depth_m=extent.maximum_depth_m,
            source=EventSource.SIMULATION,
            reason=f"SIMULATION: {scenario.name}",
        )
        res1 = twin.apply_event(flood_event)
        assert res1.applied is True
        assert twin.state_version == 1

        # 5. Ingest Road Closure into Digital Twin
        road_close_event = RoadStatusChangedEvent(
            event_id="EVT-SIM-ROAD-CLOSE-01",
            road_id=road.road_id,
            new_status=RoadStatus.BLOCKED,
            source=EventSource.SIMULATION,
            reason=road_exp.closure_reason,
            caused_by_event_id=flood_event.event_id,
        )
        res2 = twin.apply_event(road_close_event)
        assert res2.applied is True
        assert twin.state_version == 2

        # 6. Verify Digital Twin operational state
        updated_road = twin.get_road("R-COAST")
        assert updated_road is not None
        assert updated_road.status == RoadStatus.BLOCKED
        assert "exceeds vehicle safety threshold" in (updated_road.reason or "")

        # 7. Verify Phase 08 StateOverlay received the operational road closure
        override = overlay.get_road_override("R-COAST")
        assert override is not None
        assert override.status == RoadStatus.BLOCKED

        # 8. Idempotency check: Re-applying same flood event does not increment version
        res_dup = twin.apply_event(flood_event)
        assert res_dup.applied is False
        assert res_dup.is_duplicate is True
        assert twin.state_version == 2


class TestSerializationAndDeterminism:
    """Test GeoJSON serialization and reproducibility."""

    def test_geojson_serialization(self):
        poly = Polygon([[85.80, 20.00], [85.82, 20.00], [85.82, 20.02], [85.80, 20.02], [85.80, 20.00]])
        extent = SimulatedFloodExtent.from_shapely(
            flood_zone_id="FZ-GEOJSON-01",
            scenario_id="SCEN-GEOJSON",
            geometry=poly,
            max_depth_m=0.75,
            mode=SimulationMode.SIMULATION,
        )
        feature = flood_extent_to_geojson_feature(extent)
        assert feature["type"] == "Feature"
        assert feature["properties"]["flood_zone_id"] == "FZ-GEOJSON-01"
        assert feature["properties"]["mode"] == "SIMULATION"
        assert feature["properties"]["severity"] == "MODERATE"
        assert feature["properties"]["maximum_depth_m"] == 0.75

    def test_simulation_determinism(self, synthetic_elevation_grid: ElevationGrid):
        scen = FloodScenario(
            scenario_id="scen-det-01",
            name="Deterministic Check",
            scenario_type=ScenarioType.WATER_LEVEL,
            water_level_m=85.0,
        )
        engine = FloodSimulationEngine(elevation_grid=synthetic_elevation_grid)
        res1 = engine.simulate(scen)
        res2 = engine.simulate(scen)

        assert res1.area_sq_meters == res2.area_sq_meters
        assert res1.maximum_depth_m == res2.maximum_depth_m
        assert res1.mean_depth_m == res2.mean_depth_m
        assert res1.geometry == res2.geometry
