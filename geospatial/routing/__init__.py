"""
NEXUS Emergency Routing Package.

Foundational routing layer computing practical shortest-path routes across
the OSM road graph while respecting directionality, road status, accessibility,
and emergency vehicle capabilities.
"""

from geospatial.routing.constraints import EmergencyRoutingPolicy
from geospatial.routing.costs import (
    DEFAULT_SPEEDS_KMH,
    calculate_edge_cost,
    calculate_edge_duration_seconds,
    get_edge_speed_kmh,
)
from geospatial.routing.dynamic_state import (
    OverrideSource,
    RoadStateChangedEvent,
    RoadStateOverride,
)
from geospatial.routing.models import (
    RouteRequest,
    RouteResult,
    RouteSegment,
    RoutingMode,
    VehicleType,
)
from geospatial.routing.nearest_node import find_nearest_node
from geospatial.routing.rerouting import (
    DynamicRerouter,
    ReroutingExplanation,
    ReroutingResult,
)
from geospatial.routing.road_graph import RoutingGraphAdapter
from geospatial.routing.route_comparison import RouteComparison, compare_routes
from geospatial.routing.router import EmergencyRouter
from geospatial.routing.serialization import (
    route_result_to_feature_collection,
    route_result_to_geojson_feature,
)
from geospatial.routing.state_overlay import StateOverlay

__all__ = [
    "RoutingMode",
    "VehicleType",
    "RouteSegment",
    "RouteRequest",
    "RouteResult",
    "RoutingGraphAdapter",
    "EmergencyRoutingPolicy",
    "DEFAULT_SPEEDS_KMH",
    "get_edge_speed_kmh",
    "calculate_edge_duration_seconds",
    "calculate_edge_cost",
    "find_nearest_node",
    "EmergencyRouter",
    "route_result_to_geojson_feature",
    "route_result_to_feature_collection",
    "OverrideSource",
    "RoadStateOverride",
    "RoadStateChangedEvent",
    "StateOverlay",
    "RouteComparison",
    "compare_routes",
    "ReroutingExplanation",
    "ReroutingResult",
    "DynamicRerouter",
]
