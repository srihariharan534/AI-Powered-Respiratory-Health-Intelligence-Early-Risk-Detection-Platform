"""
GeoJSON Feature and FeatureCollection serialization for RouteResult.
"""

from typing import Any, Dict

from geospatial.routing.models import RouteResult


def route_result_to_geojson_feature(result: RouteResult) -> Dict[str, Any]:
    """
    Convert a RouteResult to a standard GeoJSON Feature dictionary.
    """
    return {
        "type": "Feature",
        "id": result.route_id,
        "geometry": result.geometry,
        "properties": {
            "route_id": result.route_id,
            "origin": result.origin,
            "destination": result.destination,
            "distance_meters": result.distance_meters,
            "estimated_duration_seconds": result.estimated_duration_seconds,
            "vehicle_type": result.vehicle_type.value,
            "routing_mode": result.routing_mode.value,
            "algorithm_used": result.algorithm_used,
            "snapped_origin_node": result.snapped_origin_node,
            "snapped_destination_node": result.snapped_destination_node,
            "snapped_origin_distance_meters": result.snapped_origin_distance_meters,
            "snapped_destination_distance_meters": result.snapped_destination_distance_meters,
            "path_nodes": result.path_nodes,
            "path_edges": result.path_edges,
            "warnings": result.warnings,
            "constraints_applied": result.constraints_applied,
        },
    }


def route_result_to_feature_collection(result: RouteResult) -> Dict[str, Any]:
    """
    Convert a RouteResult to a standard GeoJSON FeatureCollection dictionary.
    """
    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": [route_result_to_geojson_feature(result)],
    }
