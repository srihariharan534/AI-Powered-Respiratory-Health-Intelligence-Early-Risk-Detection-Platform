"""
NEXUS Flood Simulation Foundation and Engine.
Scenario-based flood inundation simulation and spatial exposure analysis.
"""

from geospatial.flood.comparison import (
    ScenarioComparisonResult,
    compare_scenarios,
)
from geospatial.flood.exposure import (
    FacilityExposure,
    IncidentExposure,
    PopulationExposure,
    RoadExposure,
    ScenarioExposureResult,
    VulnerabilityExposure,
    evaluate_point_facility_exposure,
    evaluate_road_exposure,
)
from geospatial.flood.extent import SimulatedFloodExtent
from geospatial.flood.model import (
    ElevationGrid,
    FloodSimulationEngine,
)
from geospatial.flood.scenario import (
    FloodScenario,
    ScenarioType,
    SimulationMode,
)
from geospatial.flood.serialization import (
    exposure_to_geojson_feature_collection,
    flood_extent_to_geojson_feature,
)
from geospatial.flood.thresholds import (
    DEFAULT_THRESHOLDS,
    FloodSeverity,
    SeverityThresholds,
    classify_flood_depth,
)

__all__ = [
    "FloodSeverity",
    "SeverityThresholds",
    "classify_flood_depth",
    "DEFAULT_THRESHOLDS",
    "FloodScenario",
    "ScenarioType",
    "SimulationMode",
    "SimulatedFloodExtent",
    "ElevationGrid",
    "FloodSimulationEngine",
    "RoadExposure",
    "FacilityExposure",
    "IncidentExposure",
    "PopulationExposure",
    "VulnerabilityExposure",
    "ScenarioExposureResult",
    "evaluate_road_exposure",
    "evaluate_point_facility_exposure",
    "ScenarioComparisonResult",
    "compare_scenarios",
    "flood_extent_to_geojson_feature",
    "exposure_to_geojson_feature_collection",
]
