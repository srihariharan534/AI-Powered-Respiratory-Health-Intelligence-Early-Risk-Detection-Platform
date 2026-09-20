"""
Unit tests for the NEXUS Emergency Routing Engine (Phase 07).
Tests Dijkstra, A*, directionality, road status, emergency accessibility, nearest node snapping,
and GeoJSON serialization against synthetic OSM road graph networks.
"""

import json
from pathlib import Path

import pytest

from geospatial.osm.roads.graph_builder import build_road_graph
from geospatial.osm.roads.parser import parse_osm_payload
from geospatial.routing.models import (
    RouteRequest,
    RoutingMode,
    VehicleType,
)
from geospatial.routing.nearest_node import find_nearest_node
from geospatial.routing.road_graph import RoutingGraphAdapter
from geospatial.routing.router import EmergencyRouter
from geospatial.routing.serialization import (
    route_result_to_feature_collection,
    route_result_to_geojson_feature,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = ROOT_DIR / "data" / "sample" / "osm" / "synthetic_osm_fixture.json"


@pytest.fixture
def synthetic_graph_adapter():
    """Build a RoutingGraphAdapter from the Phase 05 synthetic OSM fixture."""
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    nodes_map, ways = parse_osm_payload(payload)
    nx_graph, graph_def = build_road_graph(nodes_map, ways, graph_id="synthetic-osm-test")
    return RoutingGraphAdapter(nx_graph, graph_def)


def test_graph_adapter_topology(synthetic_graph_adapter):
    """Verify adapter exposes graph nodes, edges, and coordinates properly."""
    adapter = synthetic_graph_adapter
    assert adapter.node_count == 4
    assert adapter.edge_count == 7

    coords = adapter.get_node_coordinates("NODE-1001")
    assert coords is not None
    assert coords[0] == 80.2650
    assert coords[1] == 13.0810

    successors = adapter.get_successors("NODE-1002")
    # NODE-1002 connects to 1001 (bidirectional), 1003 (bidirectional), and 1004 (forward)
    assert "NODE-1001" in successors
    assert "NODE-1003" in successors
    assert "NODE-1004" in successors


def test_nearest_node_snapping(synthetic_graph_adapter):
    """Verify geographic coordinate snapping to closest road graph node."""
    adapter = synthetic_graph_adapter

    # Coordinate exactly near NODE-1001 (80.2650, 13.0810)
    node_id, dist = find_nearest_node((80.2651, 13.0811), adapter)
    assert node_id == "NODE-1001"
    assert dist < 50.0

    # Far away point exceeding max_search_radius_meters raises ValueError
    with pytest.raises(ValueError, match="No road graph node found within"):
        find_nearest_node((81.0, 14.0), adapter, max_search_radius_meters=1000.0)


def test_directionality_enforcement(synthetic_graph_adapter):
    """Verify one-way road directionality is strictly enforced."""
    adapter = synthetic_graph_adapter
    router = EmergencyRouter(adapter)

    # Way 2003 (NODE-1002 -> NODE-1004) is oneway='yes'
    # Routing 1002 -> 1004 should traverse edge directly
    req_fwd = RouteRequest(
        origin=[80.2707, 13.0827],  # NODE-1002
        destination=[80.2707, 13.0780],  # NODE-1004
        routing_mode=RoutingMode.DISTANCE,
    )
    result_fwd = router.route(req_fwd)
    assert result_fwd.path_nodes == ["NODE-1002", "NODE-1004"]

    # Routing reverse: 1004 -> 1002 CANNOT use way 2003 directly because it is one-way forward!
    # Without allow_restricted_roads/private access, no route exists (raises ValueError)
    req_rev_blocked = RouteRequest(
        origin=[80.2707, 13.0780],  # NODE-1004
        destination=[80.2707, 13.0827],  # NODE-1002
        routing_mode=RoutingMode.DISTANCE,
    )
    with pytest.raises(ValueError, match="No traversable route found"):
        router.route(req_rev_blocked)

    # Now if way 2004 accessibility is set to ALL_VEHICLES, it can traverse 1004 -> 1001 -> 1002
    # but NEVER the reverse of one-way 2003 (1004 -> 1002)
    edge_1004_1001 = adapter.get_edges_between("NODE-1004", "NODE-1001")[0]
    edge_1004_1001["accessibility"] = "ALL_VEHICLES"
    result_rev = router.route(req_rev_blocked)
    assert result_rev.path_nodes == ["NODE-1004", "NODE-1001", "NODE-1002"]


def test_dijkstra_vs_astar_equivalence(synthetic_graph_adapter):
    """Verify Dijkstra and A* return identical optimal path nodes and distances."""
    adapter = synthetic_graph_adapter
    router = EmergencyRouter(adapter)

    req_dijkstra = RouteRequest(
        origin=[80.2650, 13.0810],  # 1001
        destination=[80.2750, 13.0850],  # 1003
        routing_mode=RoutingMode.DISTANCE,
        algorithm="dijkstra",
    )
    res_dijkstra = router.route(req_dijkstra)

    req_astar = RouteRequest(
        origin=[80.2650, 13.0810],
        destination=[80.2750, 13.0850],
        routing_mode=RoutingMode.DISTANCE,
        algorithm="astar",
    )
    res_astar = router.route(req_astar)

    assert res_dijkstra.path_nodes == res_astar.path_nodes
    assert pytest.approx(res_dijkstra.distance_meters, rel=1e-3) == res_astar.distance_meters


def test_distance_vs_travel_time_mode(synthetic_graph_adapter):
    """Verify routing can optimize for travel time vs distance."""
    adapter = synthetic_graph_adapter
    router = EmergencyRouter(adapter)

    req_dist = RouteRequest(
        origin=[80.2650, 13.0810],
        destination=[80.2750, 13.0850],
        routing_mode=RoutingMode.DISTANCE,
    )
    res_dist = router.route(req_dist)

    req_time = RouteRequest(
        origin=[80.2650, 13.0810],
        destination=[80.2750, 13.0850],
        routing_mode=RoutingMode.TRAVEL_TIME,
    )
    res_time = router.route(req_time)

    assert res_dist.distance_meters > 0
    assert res_time.estimated_duration_seconds > 0
    assert res_dist.path_nodes == ["NODE-1001", "NODE-1002", "NODE-1003"]


def test_emergency_accessibility_filtering(synthetic_graph_adapter):
    """Verify emergency-only spurs are traversable by emergency vehicles."""
    adapter = synthetic_graph_adapter
    router = EmergencyRouter(adapter)

    # Way 2003 has access=emergency
    req = RouteRequest(
        origin=[80.2707, 13.0827],  # 1002
        destination=[80.2707, 13.0780],  # 1004
        vehicle_type=VehicleType.AMBULANCE,
    )
    res = router.route(req)
    assert res.path_nodes == ["NODE-1002", "NODE-1004"]


def test_blocked_road_rejection(synthetic_graph_adapter):
    """Verify BLOCKED road edges are completely avoided by routing engine."""
    adapter = synthetic_graph_adapter
    # Mark edge 1002 -> 1003 as BLOCKED
    edges_1002_1003 = adapter.get_edges_between("NODE-1002", "NODE-1003")
    assert len(edges_1002_1003) > 0
    edges_1002_1003[0]["status"] = "BLOCKED"

    router = EmergencyRouter(adapter)
    req = RouteRequest(
        origin=[80.2707, 13.0827],  # 1002
        destination=[80.2750, 13.0850],  # 1003
    )
    with pytest.raises(ValueError, match="No traversable route found"):
        router.route(req)


def test_identity_route_same_node(synthetic_graph_adapter):
    """Verify snapping to identical node returns valid zero-length route."""
    adapter = synthetic_graph_adapter
    router = EmergencyRouter(adapter)

    req = RouteRequest(
        origin=[80.2650, 13.0810],
        destination=[80.2650, 13.0810],
    )
    res = router.route(req)
    assert res.path_nodes == ["NODE-1001"]
    assert res.distance_meters == 0.0
    assert res.estimated_duration_seconds == 0.0


def test_route_geojson_serialization(synthetic_graph_adapter):
    """Verify route serialization to standard GeoJSON Feature and FeatureCollection."""
    adapter = synthetic_graph_adapter
    router = EmergencyRouter(adapter)

    req = RouteRequest(
        origin=[80.2650, 13.0810],
        destination=[80.2750, 13.0850],
    )
    res = router.route(req)

    feat = route_result_to_geojson_feature(res)
    assert feat["type"] == "Feature"
    assert feat["geometry"]["type"] == "LineString"
    assert feat["properties"]["route_id"] == res.route_id
    assert feat["properties"]["distance_meters"] == res.distance_meters

    fc = route_result_to_feature_collection(res)
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1
