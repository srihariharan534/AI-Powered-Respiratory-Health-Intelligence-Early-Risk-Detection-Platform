"""
Graph Adapter for NEXUS Emergency Routing.
Wraps NetworkX MultiDiGraph and RoadGraphDefinition to provide an isolated,
clean interface for routing algorithms without exposing raw OSM structures.
"""

from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from geospatial.osm.roads.models import RoadGraphDefinition


class RoutingGraphAdapter:
    """
    Adapter providing a clean query interface over the NEXUS road network graph.
    """

    def __init__(
        self,
        graph: nx.MultiDiGraph,
        definition: Optional[RoadGraphDefinition] = None,
        overlay: Optional[Any] = None,
    ):
        self._graph = graph
        self._overlay = overlay
        self._nodes: Dict[str, Tuple[float, float]] = {}  # node_id -> (lon, lat)
        self._edges_by_id: Dict[str, Dict[str, Any]] = {}

        # Populate node coordinates
        if definition:
            for n in definition.nodes:
                self._nodes[n.node_id] = (n.longitude, n.latitude)
            for e in definition.edges:
                self._edges_by_id[e.edge_id] = e.model_dump()
                if self._overlay is not None:
                    self._overlay.register_road_edge(e.road_id, e.edge_id, e.bridge_id)
        else:
            for node_id, data in self._graph.nodes(data=True):
                self._nodes[node_id] = (data.get("longitude", 0.0), data.get("latitude", 0.0))

        # Index all edge attributes from graph
        for u, v, key, data in self._graph.edges(keys=True, data=True):
            edge_id = data.get("edge_id", key)
            if edge_id not in self._edges_by_id:
                self._edges_by_id[edge_id] = data
                if self._overlay is not None:
                    road_id = data.get("road_id", "")
                    bridge_id = data.get("bridge_id")
                    if road_id:
                        self._overlay.register_road_edge(road_id, edge_id, bridge_id)

    @property
    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    def get_nodes(self) -> Dict[str, Tuple[float, float]]:
        """Return mapping of node_id -> (lon, lat)."""
        return dict(self._nodes)

    def get_node_coordinates(self, node_id: str) -> Optional[Tuple[float, float]]:
        """Get (longitude, latitude) of a node."""
        return self._nodes.get(node_id)

    def get_successors(self, node_id: str) -> List[str]:
        """Get downstream neighbor nodes reachable from node_id respecting edge direction."""
        if not self._graph.has_node(node_id):
            return []
        return list(self._graph.successors(node_id))

    def get_edges_between(self, u: str, v: str) -> List[Dict[str, Any]]:
        """Get all directed edge metadata dicts between node u and node v with effective overlay applied."""
        if not self._graph.has_edge(u, v):
            return []
        edge_data = self._graph.get_edge_data(u, v)
        if isinstance(edge_data, dict):
            raw_edges = list(edge_data.values())
            if self._overlay is not None:
                return [self._overlay.get_effective_edge_data(e) for e in raw_edges]
            return raw_edges
        return []

    def get_edge_by_id(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Lookup edge metadata by unique edge_id with effective overlay applied."""
        edge = self._edges_by_id.get(edge_id)
        if edge is not None and self._overlay is not None:
            return self._overlay.get_effective_edge_data(edge)
        return edge

    @property
    def overlay(self) -> Optional[Any]:
        return self._overlay

    @overlay.setter
    def overlay(self, value: Any) -> None:
        self._overlay = value
        # Re-index edges into new overlay
        if value is not None:
            for edge_id, data in self._edges_by_id.items():
                road_id = data.get("road_id", "")
                bridge_id = data.get("bridge_id")
                if road_id:
                    value.register_road_edge(road_id, edge_id, bridge_id)

    def contains_node(self, node_id: str) -> bool:
        """Check if graph contains node."""
        return self._graph.has_node(node_id)
