"""
NEXUS OpenStreetMap Data Models.
Structured representations for raw OSM elements, normalized road entities, bridges, and graphs.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class OSMNode(BaseModel):
    """Raw or parsed OSM node with geographic coordinates."""
    model_config = ConfigDict(extra="ignore")
    node_id: int
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    tags: dict[str, str] = Field(default_factory=dict)


class OSMWay(BaseModel):
    """Raw or parsed OSM way representing a linear or polygonal feature."""
    model_config = ConfigDict(extra="ignore")
    way_id: int
    nodes: list[int] = Field(..., min_length=2)
    tags: dict[str, str] = Field(default_factory=dict)


class GraphNode(BaseModel):
    """Topology graph node with geographic location."""
    model_config = ConfigDict(extra="forbid")
    node_id: str
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)


class GraphEdge(BaseModel):
    """Directed graph edge representing navigable road segment between two graph nodes."""
    model_config = ConfigDict(extra="forbid")
    edge_id: str
    source_node: str
    target_node: str
    road_id: str
    geometry: list[list[float]] = Field(..., min_length=2)  # [[lon, lat], ...]
    length_meters: float = Field(..., ge=0.0)
    directionality: Literal["forward", "backward", "bidirectional"]
    road_type: str
    accessibility: str
    speed_limit_kmh: float | None = None
    is_bridge: bool = False
    bridge_id: str | None = None


class RoadGraphDefinition(BaseModel):
    """Serializable, deterministic road network graph."""
    model_config = ConfigDict(extra="forbid")
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metadata: dict[str, Any] = Field(default_factory=dict)
