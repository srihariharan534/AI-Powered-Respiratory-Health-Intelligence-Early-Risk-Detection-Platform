"""
Edge Cost Calculations for NEXUS Emergency Routing.
Distinguishes between distance optimization and travel-time optimization.
Applies explicit fallback speeds where maxspeed is missing in OSM data.
"""

from typing import Any, Dict

from geospatial.routing.constraints import EmergencyRoutingPolicy
from geospatial.routing.models import RoutingMode

# Documented conservative urban fallback speeds in km/h when maxspeed is not tagged in OSM
DEFAULT_SPEEDS_KMH: Dict[str, float] = {
    "motorway": 80.0,
    "trunk": 60.0,
    "primary": 50.0,
    "secondary": 40.0,
    "tertiary": 30.0,
    "residential": 25.0,
    "service": 15.0,
    "living_street": 15.0,
    "bridge": 40.0,
    "culvert": 30.0,
    "unclassified": 30.0,
}
FALLBACK_SPEED_KMH = 30.0


def get_edge_speed_kmh(edge_data: Dict[str, Any]) -> float:
    """
    Determine the speed limit in km/h for an edge.
    Prioritizes explicit speed_limit_kmh, then falls back to documented default speeds by road_type.
    """
    explicit = edge_data.get("speed_limit_kmh")
    if explicit is not None and isinstance(explicit, (int, float)) and explicit > 0:
        return float(explicit)

    road_type = str(edge_data.get("road_type", "residential")).lower().strip()
    return DEFAULT_SPEEDS_KMH.get(road_type, FALLBACK_SPEED_KMH)


def calculate_edge_duration_seconds(edge_data: Dict[str, Any], length_meters: float) -> float:
    """
    Calculate traversal duration in seconds: time = distance / speed.
    """
    speed_kmh = get_edge_speed_kmh(edge_data)
    # Convert km/h to m/s: 1 km/h = 1000m / 3600s = 1/3.6 m/s
    speed_ms = max(speed_kmh / 3.6, 0.5)  # minimum 0.5 m/s safety floor
    return round(length_meters / speed_ms, 2)


def calculate_edge_cost(
    edge_data: Dict[str, Any],
    routing_mode: RoutingMode,
    policy: EmergencyRoutingPolicy,
) -> float:
    """
    Calculate the traversal cost for an edge according to the selected routing mode.
    Applies penalty multipliers for RESTRICTED status if configured.
    """
    length_meters = float(edge_data.get("length_meters", 0.0))
    if length_meters < 0:
        length_meters = 0.0

    if routing_mode == RoutingMode.DISTANCE:
        base_cost = length_meters
    elif routing_mode == RoutingMode.TRAVEL_TIME:
        base_cost = calculate_edge_duration_seconds(edge_data, length_meters)
    else:
        base_cost = length_meters

    status = str(edge_data.get("status", "OPEN")).upper()
    if status == "RESTRICTED" and policy.max_penalty_multiplier > 1.0:
        base_cost *= policy.max_penalty_multiplier

    return base_cost
