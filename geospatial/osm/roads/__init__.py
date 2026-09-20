"""
NEXUS OpenStreetMap Roads Processing Package.
"""

from geospatial.osm.roads.distance import (
    calculate_haversine_distance,
    calculate_linestring_length,
)
from geospatial.osm.roads.graph_builder import build_road_graph, parse_oneway_tag
from geospatial.osm.roads.models import (
    GraphEdge,
    GraphNode,
    OSMNode,
    OSMWay,
    RoadGraphDefinition,
)
from geospatial.osm.roads.normalizer import (
    normalize_accessibility,
    normalize_osm_way_to_road,
    normalize_speed_limit,
)
from geospatial.osm.roads.parser import parse_osm_payload

__all__ = [
    "OSMNode",
    "OSMWay",
    "GraphNode",
    "GraphEdge",
    "RoadGraphDefinition",
    "parse_osm_payload",
    "normalize_speed_limit",
    "normalize_accessibility",
    "normalize_osm_way_to_road",
    "calculate_haversine_distance",
    "calculate_linestring_length",
    "parse_oneway_tag",
    "build_road_graph",
]
