"""
Data models and types for the NEXUS Emergency Routing Engine.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RoutingMode(str, Enum):
    """Routing optimization objective."""
    DISTANCE = "DISTANCE"
    TRAVEL_TIME = "TRAVEL_TIME"


class VehicleType(str, Enum):
    """Emergency vehicle classification."""
    GENERAL_EMERGENCY = "GENERAL_EMERGENCY"
    AMBULANCE = "AMBULANCE"
    FIRE_RESPONSE = "FIRE_RESPONSE"
    RESCUE_VEHICLE = "RESCUE_VEHICLE"


class RouteSegment(BaseModel):
    """Metrics and geometry for an individual traversed edge in a route."""
    model_config = ConfigDict(extra="forbid")
    edge_id: str
    road_id: str
    source_node: str
    target_node: str
    length_meters: float = Field(..., ge=0.0)
    duration_seconds: float = Field(..., ge=0.0)
    road_type: str
    speed_limit_kmh: Optional[float] = None
    geometry: List[List[float]] = Field(..., min_length=2)  # [[lon, lat], ...]


class RouteRequest(BaseModel):
    """Request payload for an emergency route calculation."""
    model_config = ConfigDict(extra="forbid")
    origin: List[float] = Field(..., min_length=2, max_length=2)  # [lon, lat]
    destination: List[float] = Field(..., min_length=2, max_length=2)  # [lon, lat]
    vehicle_type: VehicleType = VehicleType.GENERAL_EMERGENCY
    routing_mode: RoutingMode = RoutingMode.TRAVEL_TIME
    max_search_radius_meters: float = Field(default=2500.0, gt=0.0)
    allow_restricted_roads: bool = True
    allow_unknown_roads: bool = True
    allow_private_roads: bool = False
    algorithm: str = "dijkstra"  # "dijkstra" or "astar"


class RouteResult(BaseModel):
    """Comprehensive route computation result."""
    model_config = ConfigDict(extra="forbid")
    route_id: str
    origin: List[float]  # [lon, lat]
    destination: List[float]  # [lon, lat]
    snapped_origin_node: str
    snapped_destination_node: str
    snapped_origin_distance_meters: float
    snapped_destination_distance_meters: float
    path_nodes: List[str]
    path_edges: List[str]
    segments: List[RouteSegment]
    geometry: Dict[str, Any]  # GeoJSON LineString
    distance_meters: float = Field(..., ge=0.0)
    estimated_duration_seconds: float = Field(..., ge=0.0)
    vehicle_type: VehicleType
    routing_mode: RoutingMode
    algorithm_used: str
    constraints_applied: List[str]
    warnings: List[str] = Field(default_factory=list)
    state_version: int = 1
    request: Optional[RouteRequest] = None
