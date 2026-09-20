"""
NEXUS Flood Simulation - GeoJSON Serialization.
Provides standardized, schema-compliant GeoJSON Feature and FeatureCollection
serialization for simulated flood extents and infrastructure exposures.
"""

from typing import Any, Dict, List

from geospatial.flood.exposure import ScenarioExposureResult
from geospatial.flood.extent import SimulatedFloodExtent


def flood_extent_to_geojson_feature(extent: SimulatedFloodExtent) -> Dict[str, Any]:
    """Serializes a SimulatedFloodExtent to a standard GeoJSON Feature."""
    return {
        "type": "Feature",
        "geometry": extent.geometry,
        "properties": {
            "flood_zone_id": extent.flood_zone_id,
            "scenario_id": extent.scenario_id,
            "mode": extent.mode.value,
            "severity": extent.severity.value,
            "maximum_depth_m": extent.maximum_depth_m,
            "mean_depth_m": extent.mean_depth_m,
            "area_sq_meters": extent.area_sq_meters,
            "created_at": extent.created_at.isoformat(),
            "source": extent.source,
            **extent.metadata,
        },
    }


def exposure_to_geojson_feature_collection(
    extent: SimulatedFloodExtent,
    exposure: ScenarioExposureResult,
) -> Dict[str, Any]:
    """
    Serializes a complete exposure analysis result into a GeoJSON FeatureCollection.
    Includes the flood boundary feature followed by affected roads and facilities.
    """
    features: List[Dict[str, Any]] = [flood_extent_to_geojson_feature(extent)]

    # Add affected road summary items
    for road in exposure.affected_roads:
        if road.affected:
            features.append({
                "type": "Feature",
                "geometry": None,  # Geometry referenced by road_id
                "properties": {
                    "feature_type": "AFFECTED_ROAD",
                    "road_id": road.road_id,
                    "submerged_length_meters": road.submerged_length_meters,
                    "estimated_depth_m": road.estimated_depth_m,
                    "closure_recommended": road.closure_recommended,
                    "closure_reason": road.closure_reason,
                    "scenario_id": exposure.scenario_id,
                    "mode": exposure.mode,
                },
            })

    # Add affected facility items
    for fac in exposure.affected_hospitals + exposure.affected_shelters + exposure.affected_bridges:
        if fac.affected:
            features.append({
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "feature_type": f"AFFECTED_{fac.facility_type}",
                    "facility_id": fac.facility_id,
                    "name": fac.name,
                    "estimated_depth_m": fac.estimated_depth_m,
                    "scenario_id": exposure.scenario_id,
                    "mode": exposure.mode,
                },
            })

    return {
        "type": "FeatureCollection",
        "properties": {
            "scenario_id": exposure.scenario_id,
            "mode": exposure.mode,
            "total_flooded_area_m2": exposure.total_flooded_area_m2,
            "total_roads_affected": exposure.total_roads_affected,
            "total_facilities_affected": exposure.total_facilities_affected,
        },
        "features": features,
    }
