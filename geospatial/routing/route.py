"""
Path Reconstruction and Geometry Assembly for Computed Routes.
"""

import uuid
from typing import Any, Dict, List

from geospatial.routing.costs import calculate_edge_duration_seconds
from geospatial.routing.models import (
    RouteRequest,
    RouteResult,
    RouteSegment,
)
from geospatial.routing.road_graph import RoutingGraphAdapter


def reconstruct_route(
    request: RouteRequest,
    graph_adapter: RoutingGraphAdapter,
    path_nodes: List[str],
    chosen_edges: List[Dict[str, Any]],
    snapped_origin_id: str,
    snapped_destination_id: str,
    origin_snap_dist: float,
    dest_snap_dist: float,
    algorithm_used: str,
    warnings: List[str],
) -> RouteResult:
    """
    Reconstruct full RouteResult from the list of traversed nodes and chosen edges.
    Assembles continuous GeoJSON LineString coordinates.
    """
    route_id = f"ROUTE-{uuid.uuid4().hex[:8].upper()}"

    segments: List[RouteSegment] = []
    accumulated_coords: List[List[float]] = []
    total_length_meters = 0.0
    total_duration_seconds = 0.0
    path_edge_ids: List[str] = []

    for edge_data in chosen_edges:
        edge_id = str(edge_data.get("edge_id", ""))
        road_id = str(edge_data.get("road_id", ""))
        u = str(edge_data.get("source_node", ""))
        v = str(edge_data.get("target_node", ""))
        length_m = float(edge_data.get("length_meters", 0.0))
        duration_s = calculate_edge_duration_seconds(edge_data, length_m)
        road_type = str(edge_data.get("road_type", "residential"))
        speed_limit = edge_data.get("speed_limit_kmh")
        geom = edge_data.get("geometry", [])

        total_length_meters += length_m
        total_duration_seconds += duration_s
        path_edge_ids.append(edge_id)

        segments.append(
            RouteSegment(
                edge_id=edge_id,
                road_id=road_id,
                source_node=u,
                target_node=v,
                length_meters=length_m,
                duration_seconds=duration_s,
                road_type=road_type,
                speed_limit_kmh=speed_limit,
                geometry=geom,
            )
        )

        # Append coordinates preserving continuity
        for pt in geom:
            if not accumulated_coords or accumulated_coords[-1] != pt:
                accumulated_coords.append(pt)

    # If origin and destination snap to the same node with no edges
    if not accumulated_coords and path_nodes:
        node_coords = graph_adapter.get_node_coordinates(path_nodes[0])
        if node_coords:
            accumulated_coords = [[node_coords[0], node_coords[1]]]

    geojson_line: Dict[str, Any] = {
        "type": "LineString",
        "coordinates": accumulated_coords,
    }

    constraints_applied = [
        f"Vehicle: {request.vehicle_type.value}",
        f"Objective: {request.routing_mode.value}",
        f"Allow Restricted: {request.allow_restricted_roads}",
        f"Allow Unknown: {request.allow_unknown_roads}",
    ]

    return RouteResult(
        route_id=route_id,
        origin=request.origin,
        destination=request.destination,
        snapped_origin_node=snapped_origin_id,
        snapped_destination_node=snapped_destination_id,
        snapped_origin_distance_meters=round(origin_snap_dist, 2),
        snapped_destination_distance_meters=round(dest_snap_dist, 2),
        path_nodes=path_nodes,
        path_edges=path_edge_ids,
        segments=segments,
        geometry=geojson_line,
        distance_meters=round(total_length_meters, 2),
        estimated_duration_seconds=round(total_duration_seconds, 2),
        vehicle_type=request.vehicle_type,
        routing_mode=request.routing_mode,
        algorithm_used=algorithm_used,
        constraints_applied=constraints_applied,
        warnings=warnings,
        state_version=graph_adapter.overlay.version if graph_adapter.overlay is not None else 1,
        request=request,
    )
