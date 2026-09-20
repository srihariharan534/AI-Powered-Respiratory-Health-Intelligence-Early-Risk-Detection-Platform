"""
Unit tests for geospatial coordinate ordering and geodesic distance conventions.
"""

from geospatial.osm.roads.distance import (
    calculate_haversine_distance,
    calculate_linestring_length,
)
from geospatial.osm.roads.models import GraphNode, OSMNode


def test_coordinate_convention_longitude_first():
    """Verify nodes store coordinates with longitude first, then latitude."""
    osm_node = OSMNode(node_id=1, longitude=80.2707, latitude=13.0827)
    assert osm_node.longitude == 80.2707
    assert osm_node.latitude == 13.0827

    graph_node = GraphNode(node_id="NODE-1", longitude=80.2707, latitude=13.0827)
    assert graph_node.longitude == 80.2707
    assert graph_node.latitude == 13.0827


def test_haversine_distance_computation():
    """Verify Haversine formula produces accurate geodesic metric distances."""
    # Distance between (80.2650, 13.0810) and (80.2707, 13.0827) in Chennai is ~645 meters
    dist = calculate_haversine_distance(80.2650, 13.0810, 80.2707, 13.0827)
    assert 600.0 < dist < 700.0


def test_linestring_cumulative_length():
    """Verify LineString length accumulates distance across multiple segments."""
    coords = [
        [80.2650, 13.0810],
        [80.2707, 13.0827],
        [80.2750, 13.0850],
    ]
    length = calculate_linestring_length(coords)
    assert length > 1000.0
