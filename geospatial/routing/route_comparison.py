"""
Route Comparison Component for NEXUS Emergency Routing (Phase 08).
Computes quantitative deltas and topological changes between an initial route and a rerouted path.
"""

from typing import List

from pydantic import BaseModel, ConfigDict

from geospatial.routing.models import RouteResult


class RouteComparison(BaseModel):
    """
    Structured comparison between an initial route and an updated/rerouted route.
    """
    model_config = ConfigDict(extra="forbid")
    route_changed: bool
    distance_delta_meters: float
    duration_delta_seconds: float
    old_distance_meters: float
    new_distance_meters: float
    old_duration_seconds: float
    new_duration_seconds: float
    removed_edges: List[str]
    added_edges: List[str]
    shared_edges: List[str]
    removed_nodes: List[str]
    added_nodes: List[str]
    shared_nodes: List[str]


def compare_routes(old_route: RouteResult, new_route: RouteResult) -> RouteComparison:
    """
    Compare two routes and compute metric differences and edge/node sets.
    """
    old_edges = set(old_route.path_edges)
    new_edges = set(new_route.path_edges)

    removed_edges = sorted(old_edges - new_edges)
    added_edges = sorted(new_edges - old_edges)
    shared_edges = sorted(old_edges & new_edges)

    old_nodes = set(old_route.path_nodes)
    new_nodes = set(new_route.path_nodes)

    removed_nodes = sorted(old_nodes - new_nodes)
    added_nodes = sorted(new_nodes - old_nodes)
    shared_nodes = sorted(old_nodes & new_nodes)

    route_changed = (old_route.path_nodes != new_route.path_nodes) or (
        old_route.path_edges != new_route.path_edges
    )

    dist_delta = round(new_route.distance_meters - old_route.distance_meters, 2)
    dur_delta = round(new_route.estimated_duration_seconds - old_route.estimated_duration_seconds, 2)

    return RouteComparison(
        route_changed=route_changed,
        distance_delta_meters=dist_delta,
        duration_delta_seconds=dur_delta,
        old_distance_meters=old_route.distance_meters,
        new_distance_meters=new_route.distance_meters,
        old_duration_seconds=old_route.estimated_duration_seconds,
        new_duration_seconds=new_route.estimated_duration_seconds,
        removed_edges=removed_edges,
        added_edges=added_edges,
        shared_edges=shared_edges,
        removed_nodes=removed_nodes,
        added_nodes=added_nodes,
        shared_nodes=shared_nodes,
    )
