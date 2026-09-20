"""
Nearest Road Node Snapping.
Finds the closest navigable road node to an arbitrary origin/destination coordinate.
Uses Phase 06 geospatial distance calculations for geodesic precision.
"""

from typing import Optional, Tuple

from shapely.geometry import Point

from geospatial.routing.road_graph import RoutingGraphAdapter
from geospatial.spatial_analysis.distance import distance_meters
from geospatial.spatial_analysis.validation import validate_coordinates


def find_nearest_node(
    coordinates: Tuple[float, float],
    graph_adapter: RoutingGraphAdapter,
    max_search_radius_meters: float = 2500.0,
) -> Tuple[str, float]:
    """
    Find the closest road graph node to the given (longitude, latitude) coordinate.

    Args:
        coordinates: (longitude, latitude) tuple.
        graph_adapter: Validated RoutingGraphAdapter instance.
        max_search_radius_meters: Maximum allowed distance cutoff in meters.

    Returns:
        (nearest_node_id, distance_meters)

    Raises:
        ValueError: If coordinates are out of bounds, graph is empty, or no node
                    is found within max_search_radius_meters.
    """
    lon, lat = coordinates[0], coordinates[1]
    validate_coordinates(lon, lat)

    nodes = graph_adapter.get_nodes()
    if not nodes:
        raise ValueError("Cannot snap to nearest node: Road graph contains no nodes.")

    origin_point = Point(lon, lat)
    best_node_id: Optional[str] = None
    min_dist = float("inf")

    # Deterministic tie-breaking: sort candidate node_ids lexicographically
    sorted_node_items = sorted(nodes.items(), key=lambda item: item[0])

    for node_id, (node_lon, node_lat) in sorted_node_items:
        node_point = Point(node_lon, node_lat)
        dist = distance_meters(origin_point, node_point)
        if dist < min_dist:
            min_dist = dist
            best_node_id = node_id

    if best_node_id is None or min_dist > max_search_radius_meters:
        raise ValueError(
            f"No road graph node found within {max_search_radius_meters}m of ({lon}, {lat}). "
            f"Closest node '{best_node_id}' is {min_dist:.1f}m away."
        )

    return best_node_id, min_dist
