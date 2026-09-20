"""
Core Emergency Routing Engine for NEXUS.
Implements deterministic Dijkstra and A* shortest-path solvers on top of RoutingGraphAdapter.
Respects directionality, road status, accessibility, and emergency vehicle constraints.
"""

import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

from shapely.geometry import Point

from geospatial.routing.constraints import EmergencyRoutingPolicy
from geospatial.routing.costs import calculate_edge_cost
from geospatial.routing.models import (
    RouteRequest,
    RouteResult,
    RoutingMode,
)
from geospatial.routing.nearest_node import find_nearest_node
from geospatial.routing.road_graph import RoutingGraphAdapter
from geospatial.routing.route import reconstruct_route
from geospatial.spatial_analysis.distance import distance_meters


class EmergencyRouter:
    """
    High-reliability, deterministic routing solver for emergency vehicle dispatch.
    """

    def __init__(
        self,
        graph_adapter: RoutingGraphAdapter,
        policy: Optional[EmergencyRoutingPolicy] = None,
    ):
        self.graph = graph_adapter
        self.policy = policy or EmergencyRoutingPolicy()

    def route(self, request: RouteRequest) -> RouteResult:
        """
        Compute optimal emergency route for the given RouteRequest.
        """
        # 1. Snap origin and destination coordinates to closest graph nodes
        origin_node, origin_snap_dist = find_nearest_node(
            (request.origin[0], request.origin[1]),
            self.graph,
            max_search_radius_meters=request.max_search_radius_meters,
        )
        dest_node, dest_snap_dist = find_nearest_node(
            (request.destination[0], request.destination[1]),
            self.graph,
            max_search_radius_meters=request.max_search_radius_meters,
        )

        warnings: List[str] = []
        if origin_snap_dist > 500.0:
            warnings.append(
                f"Origin is {origin_snap_dist:.0f}m away from the nearest road network node."
            )
        if dest_snap_dist > 500.0:
            warnings.append(
                f"Destination is {dest_snap_dist:.0f}m away from the nearest road network node."
            )

        # 2. Trivial case: origin and destination snap to the identical node
        if origin_node == dest_node:
            return reconstruct_route(
                request=request,
                graph_adapter=self.graph,
                path_nodes=[origin_node],
                chosen_edges=[],
                snapped_origin_id=origin_node,
                snapped_destination_id=dest_node,
                origin_snap_dist=origin_snap_dist,
                dest_snap_dist=dest_snap_dist,
                algorithm_used="identity",
                warnings=warnings,
            )

        # 3. Configure routing policy from request flags
        effective_policy = EmergencyRoutingPolicy(
            allow_blocked_roads=False,
            allow_restricted_roads=request.allow_restricted_roads,
            allow_unknown_roads=request.allow_unknown_roads,
            allow_emergency_only=True,
            allow_private_roads=request.allow_private_roads,
        )

        # 4. Execute selected shortest-path algorithm
        algo = request.algorithm.lower().strip()
        if algo == "astar":
            path_nodes, chosen_edges = self._solve_astar(
                source=origin_node,
                target=dest_node,
                request=request,
                policy=effective_policy,
            )
        else:
            path_nodes, chosen_edges = self._solve_dijkstra(
                source=origin_node,
                target=dest_node,
                request=request,
                policy=effective_policy,
            )

        if not path_nodes:
            raise ValueError(
                f"No traversable route found between {origin_node} and {dest_node} "
                f"under vehicle constraints ({request.vehicle_type.value})."
            )

        return reconstruct_route(
            request=request,
            graph_adapter=self.graph,
            path_nodes=path_nodes,
            chosen_edges=chosen_edges,
            snapped_origin_id=origin_node,
            snapped_destination_id=dest_node,
            origin_snap_dist=origin_snap_dist,
            dest_snap_dist=dest_snap_dist,
            algorithm_used=algo,
            warnings=warnings,
        )

    def _solve_dijkstra(
        self,
        source: str,
        target: str,
        request: RouteRequest,
        policy: EmergencyRoutingPolicy,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Dijkstra's shortest-path algorithm with deterministic tie-breaking.
        """
        # Min-heap entries: (cost, node_id)
        queue: List[Tuple[float, str]] = [(0.0, source)]
        dist: Dict[str, float] = {source: 0.0}
        parent_node: Dict[str, str] = {}
        parent_edge: Dict[str, Dict[str, Any]] = {}
        visited: Set[str] = set()

        while queue:
            current_cost, u = heapq.heappop(queue)

            if u in visited:
                continue
            visited.add(u)

            if u == target:
                break

            # Deterministically iterate through sorted successors
            for v in sorted(self.graph.get_successors(u)):
                # Evaluate directed edges between u and v
                candidate_edges = self.graph.get_edges_between(u, v)

                # Filter traversable edges
                traversable = []
                for edge in candidate_edges:
                    ok, _ = policy.evaluate_edge_traversability(edge, request.vehicle_type)
                    if ok:
                        edge_weight = calculate_edge_cost(edge, request.routing_mode, policy)
                        traversable.append((edge_weight, edge))

                if not traversable:
                    continue

                # Pick minimum-cost edge between u and v (deterministic tie-break by edge_id)
                traversable.sort(key=lambda item: (item[0], str(item[1].get("edge_id", ""))))
                best_edge_cost, best_edge = traversable[0]

                new_cost = current_cost + best_edge_cost
                if new_cost < dist.get(v, float("inf")):
                    dist[v] = new_cost
                    parent_node[v] = u
                    parent_edge[v] = best_edge
                    heapq.heappush(queue, (new_cost, v))

        if target not in parent_node and source != target:
            return [], []

        # Reconstruct path
        path_nodes: List[str] = []
        path_edges: List[Dict[str, Any]] = []
        curr = target
        while curr != source:
            path_nodes.append(curr)
            path_edges.append(parent_edge[curr])
            curr = parent_node[curr]
        path_nodes.append(source)

        path_nodes.reverse()
        path_edges.reverse()
        return path_nodes, path_edges

    def _solve_astar(
        self,
        source: str,
        target: str,
        request: RouteRequest,
        policy: EmergencyRoutingPolicy,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        A* search algorithm with an admissible, monotonic geodesic heuristic.
        - Distance mode: Great circle Haversine straight-line distance (never overestimates).
        - Travel-time mode: Straight-line distance / max permissible speed (120 km/h = 33.33 m/s)
          (never overestimates travel time).
        """
        dest_coords = self.graph.get_node_coordinates(target)
        if not dest_coords:
            return self._solve_dijkstra(source, target, request, policy)

        dest_pt = Point(dest_coords[0], dest_coords[1])
        max_speed_ms = 120.0 / 3.6  # 33.33 m/s upper bound across network

        def heuristic(node_id: str) -> float:
            coords = self.graph.get_node_coordinates(node_id)
            if not coords:
                return 0.0
            straight_line_meters = distance_meters(Point(coords[0], coords[1]), dest_pt)
            if request.routing_mode == RoutingMode.DISTANCE:
                return straight_line_meters
            # travel time heuristic
            return straight_line_meters / max_speed_ms

        queue: List[Tuple[float, float, str]] = [(heuristic(source), 0.0, source)]
        g_score: Dict[str, float] = {source: 0.0}
        parent_node: Dict[str, str] = {}
        parent_edge: Dict[str, Dict[str, Any]] = {}
        visited: Set[str] = set()

        while queue:
            f_cost, current_g, u = heapq.heappop(queue)

            if u in visited:
                continue
            visited.add(u)

            if u == target:
                break

            for v in sorted(self.graph.get_successors(u)):
                candidate_edges = self.graph.get_edges_between(u, v)
                traversable = []
                for edge in candidate_edges:
                    ok, _ = policy.evaluate_edge_traversability(edge, request.vehicle_type)
                    if ok:
                        edge_weight = calculate_edge_cost(edge, request.routing_mode, policy)
                        traversable.append((edge_weight, edge))

                if not traversable:
                    continue

                traversable.sort(key=lambda item: (item[0], str(item[1].get("edge_id", ""))))
                best_edge_cost, best_edge = traversable[0]

                tentative_g = current_g + best_edge_cost
                if tentative_g < g_score.get(v, float("inf")):
                    g_score[v] = tentative_g
                    parent_node[v] = u
                    parent_edge[v] = best_edge
                    f_score = tentative_g + heuristic(v)
                    heapq.heappush(queue, (f_score, tentative_g, v))

        if target not in parent_node and source != target:
            return [], []

        path_nodes: List[str] = []
        path_edges: List[Dict[str, Any]] = []
        curr = target
        while curr != source:
            path_nodes.append(curr)
            path_edges.append(parent_edge[curr])
            curr = parent_node[curr]
        path_nodes.append(source)

        path_nodes.reverse()
        path_edges.reverse()
        return path_nodes, path_edges
