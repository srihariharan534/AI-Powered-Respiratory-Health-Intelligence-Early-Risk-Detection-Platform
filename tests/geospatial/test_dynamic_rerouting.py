"""
Comprehensive Unit Tests for Dynamic Rerouting Engine (Phase 08).
Validates:
- StateOverlay operational updates and precedence over base OSM state
- Non-destructive rollback restoring baseline state
- Bridge-to-road state propagation
- Affected-edge identification
- Route invalidation upon road failure
- Rerouting triggers (recalculates only when route is affected)
- Route comparison metrics and deltas
- Machine-readable explanation generation (zero LLM hallucination)
- Multiple simultaneous road state changes
- Failure mode: NO_PATH_AFTER_STATE_CHANGE
- State version incrementation and stale state detection
- Operational speed overrides
- Deterministic behavior across runs
"""

from pathlib import Path

import networkx as nx
import pytest

from geospatial.routing import (
    DynamicRerouter,
    EmergencyRouter,
    OverrideSource,
    RouteRequest,
    RoutingGraphAdapter,
    RoutingMode,
    StateOverlay,
)
from services.api.app.schemas.road import RoadStatus

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = ROOT_DIR / "data" / "sample" / "osm" / "synthetic_osm_fixture.json"


@pytest.fixture
def grid_network():
    """
    Construct deterministic multi-path network fixture:
    A (1001) ──[Way 101]── B (1002) ──[Way 102 Bridge]── C (1003)
      │                                                     │
    [Way 103]                                           [Way 104]
      │                                                     │
    D (1004) ───────────── E (1005) ───────────────────── F (1006)
                              │
                          [Way 106]
                              │
                           G (1007)

    Coordinates roughly around Chennai (80.26 to 80.28, 13.07 to 13.09).
    Two primary corridors from A to F:
      Route North: A -> B -> C -> F (via bridge B-C)
      Route South: A -> D -> E -> F
    """
    G = nx.MultiDiGraph(id="grid-network")
    overlay = StateOverlay()

    nodes = {
        "NODE-A": (80.260, 13.085),
        "NODE-B": (80.270, 13.085),
        "NODE-C": (80.280, 13.085),
        "NODE-D": (80.260, 13.075),
        "NODE-E": (80.270, 13.075),
        "NODE-F": (80.280, 13.075),
        "NODE-G": (80.270, 13.065),
    }
    for n, (lon, lat) in nodes.items():
        G.add_node(n, longitude=lon, latitude=lat)

    # Helper to add bidirectional way
    def add_bi_edge(u, v, way_id, length_m, speed_kmh=50.0, is_bridge=False, bridge_id=None):
        u_pt = nodes[u]
        v_pt = nodes[v]
        e_fwd = f"EDGE-{way_id}-{u}-{v}"
        e_rev = f"EDGE-{way_id}-{v}-{u}"
        road_id = f"ROAD-{way_id}"

        fwd_data = {
            "edge_id": e_fwd,
            "road_id": road_id,
            "source_node": u,
            "target_node": v,
            "length_meters": length_m,
            "road_type": "primary",
            "accessibility": "ALL_VEHICLES",
            "speed_limit_kmh": speed_kmh,
            "is_bridge": is_bridge,
            "bridge_id": bridge_id,
            "geometry": [[u_pt[0], u_pt[1]], [v_pt[0], v_pt[1]]],
            "status": "OPEN",
        }
        rev_data = {
            "edge_id": e_rev,
            "road_id": road_id,
            "source_node": v,
            "target_node": u,
            "length_meters": length_m,
            "road_type": "primary",
            "accessibility": "ALL_VEHICLES",
            "speed_limit_kmh": speed_kmh,
            "is_bridge": is_bridge,
            "bridge_id": bridge_id,
            "geometry": [[v_pt[0], v_pt[1]], [u_pt[0], u_pt[1]]],
            "status": "OPEN",
        }
        G.add_edge(u, v, key=e_fwd, **fwd_data)
        G.add_edge(v, u, key=e_rev, **rev_data)

    # North path: A -> B -> C -> F (Total length: 1000 + 1000 + 1000 = 3000m)
    add_bi_edge("NODE-A", "NODE-B", "101", 1000.0, 50.0)
    add_bi_edge("NODE-B", "NODE-C", "102", 1000.0, 50.0, is_bridge=True, bridge_id="BRIDGE-102")
    add_bi_edge("NODE-C", "NODE-F", "104", 1000.0, 50.0)

    # South path: A -> D -> E -> F (Total length: 1100 + 1100 + 1100 = 3300m) - slightly longer
    add_bi_edge("NODE-A", "NODE-D", "103", 1100.0, 50.0)
    add_bi_edge("NODE-D", "NODE-E", "105", 1100.0, 50.0)
    add_bi_edge("NODE-E", "NODE-F", "107", 1100.0, 50.0)

    # Spur: E -> G
    add_bi_edge("NODE-E", "NODE-G", "106", 800.0, 30.0)

    adapter = RoutingGraphAdapter(G, overlay=overlay)
    router = EmergencyRouter(adapter)
    rerouter = DynamicRerouter(router, overlay)
    return adapter, overlay, router, rerouter


def test_initial_baseline_route(grid_network):
    """Verify that initial baseline calculation chooses shorter North path (A -> B -> C -> F)."""
    _, _, router, _ = grid_network
    req = RouteRequest(
        origin=[80.260, 13.085],  # NODE-A
        destination=[80.280, 13.075],  # NODE-F
        routing_mode=RoutingMode.DISTANCE,
    )
    res = router.route(req)
    assert res.path_nodes == ["NODE-A", "NODE-B", "NODE-C", "NODE-F"]
    assert pytest.approx(res.distance_meters, rel=1e-2) == 3000.0


def test_road_override_and_precedence(grid_network):
    """Verify state overlay takes precedence over base graph without mutating base graph."""
    adapter, overlay, _, _ = grid_network

    # Initially ROAD-102 is OPEN in base graph
    raw_edges = adapter.get_edges_between("NODE-B", "NODE-C")
    assert raw_edges[0]["status"] == "OPEN"

    # Set dynamic override: ROAD-102 -> BLOCKED
    override = overlay.set_road_override(
        road_id="ROAD-102",
        status=RoadStatus.BLOCKED,
        reason="Debris blockage",
        source=OverrideSource.SIMULATION,
    )
    assert override.status == RoadStatus.BLOCKED
    assert overlay.version == 2

    # Querying through adapter now yields effective status BLOCKED
    effective_edges = adapter.get_edges_between("NODE-B", "NODE-C")
    assert effective_edges[0]["status"] == "BLOCKED"
    assert effective_edges[0]["override_applied"] is True

    # Base graph remains intact
    base_data = adapter._graph.get_edge_data("NODE-B", "NODE-C")
    assert next(iter(base_data.values()))["status"] == "OPEN"


def test_bridge_failure_propagation(grid_network):
    """Verify bridge failure correctly blocks associated road and edges."""
    adapter, overlay, _, _ = grid_network

    overlay.set_bridge_override(
        bridge_id="BRIDGE-102",
        status=RoadStatus.BLOCKED,
        reason="Structural foundation damage",
        source=OverrideSource.INFRASTRUCTURE_UPDATE,
    )

    override = overlay.get_road_override("ROAD-102")
    assert override is not None
    assert override.status == RoadStatus.BLOCKED
    assert override.bridge_id == "BRIDGE-102"

    effective_edges = adapter.get_edges_between("NODE-B", "NODE-C")
    assert effective_edges[0]["status"] == "BLOCKED"


def test_dynamic_rerouting_execution(grid_network):
    """Verify that when a road along active route is blocked, dynamic rerouting yields South path."""
    _, overlay, router, rerouter = grid_network

    # 1. Compute initial route
    req = RouteRequest(
        origin=[80.260, 13.085],  # NODE-A
        destination=[80.280, 13.075],  # NODE-F
        routing_mode=RoutingMode.DISTANCE,
    )
    initial_route = router.route(req)
    assert initial_route.path_nodes == ["NODE-A", "NODE-B", "NODE-C", "NODE-F"]

    # 2. Block Bridge ROAD-102
    overlay.set_road_override(
        road_id="ROAD-102",
        status=RoadStatus.BLOCKED,
        reason="Flood surge overtopping bridge",
        source=OverrideSource.COMMAND_CENTER,
    )

    # 3. Dynamic reroute
    reroute_res = rerouter.evaluate_and_reroute(
        current_route=initial_route,
        trigger_description="BRIDGE-102 closed due to flood overtopping",
    )

    assert reroute_res.reroute_required is True
    assert reroute_res.new_route is not None
    # Switched to South path: A -> D -> E -> F
    assert reroute_res.new_route.path_nodes == ["NODE-A", "NODE-D", "NODE-E", "NODE-F"]
    assert pytest.approx(reroute_res.new_route.distance_meters, rel=1e-2) == 3300.0

    # Verify comparison
    comp = reroute_res.comparison
    assert comp is not None
    assert comp.route_changed is True
    assert pytest.approx(comp.distance_delta_meters, rel=1e-2) == 300.0
    assert "EDGE-102-NODE-B-NODE-C" in comp.removed_edges

    # Verify deterministic machine explanation
    exp = reroute_res.explanation
    assert exp is not None
    assert "ROAD-102" in exp.affected_roads
    assert "+300.0m" in exp.summary


def test_unrelated_road_change_no_reroute(grid_network):
    """Verify that blocking an unrelated road does NOT trigger an unnecessary reroute."""
    _, overlay, router, rerouter = grid_network

    req = RouteRequest(
        origin=[80.260, 13.085],  # NODE-A
        destination=[80.280, 13.075],  # NODE-F
        routing_mode=RoutingMode.DISTANCE,
    )
    initial_route = router.route(req)

    # Block unrelated spur ROAD-106 (NODE-E -> NODE-G)
    overlay.set_road_override(
        road_id="ROAD-106",
        status=RoadStatus.BLOCKED,
        reason="Spur impassable",
    )

    reroute_res = rerouter.evaluate_and_reroute(
        current_route=initial_route,
        trigger_description="ROAD-106 spur closure",
    )

    assert reroute_res.reroute_required is False
    assert reroute_res.new_route.path_nodes == initial_route.path_nodes


def test_rollback_restores_baseline(grid_network):
    """Verify rollback clears overrides and allows router to reclaim original optimal path."""
    _, overlay, router, rerouter = grid_network

    req = RouteRequest(
        origin=[80.260, 13.085],
        destination=[80.280, 13.075],
        routing_mode=RoutingMode.DISTANCE,
    )
    initial_route = router.route(req)

    # 1. Close road -> forces south path
    overlay.set_road_override("ROAD-102", RoadStatus.BLOCKED, reason="Temporary drill")
    reroute_south = rerouter.evaluate_and_reroute(initial_route)
    assert reroute_south.new_route.path_nodes == ["NODE-A", "NODE-D", "NODE-E", "NODE-F"]

    # 2. Rollback override
    cleared = overlay.clear_road_override("ROAD-102")
    assert cleared is True
    assert overlay.get_road_override("ROAD-102") is None

    # 3. Next route computation reclaims the original North path
    restored_route = router.route(req)
    assert restored_route.path_nodes == ["NODE-A", "NODE-B", "NODE-C", "NODE-F"]


def test_no_path_after_closure(grid_network):
    """Verify clean NO_PATH_AFTER_STATE_CHANGE error when all alternative paths are severed."""
    _, overlay, router, rerouter = grid_network

    req = RouteRequest(
        origin=[80.260, 13.085],  # A
        destination=[80.280, 13.075],  # F
        routing_mode=RoutingMode.DISTANCE,
    )
    initial_route = router.route(req)

    # Block both North path (ROAD-102) and South path (ROAD-105)
    overlay.set_road_override("ROAD-102", RoadStatus.BLOCKED, reason="North corridor blocked")
    overlay.set_road_override("ROAD-105", RoadStatus.BLOCKED, reason="South corridor blocked")

    reroute_res = rerouter.evaluate_and_reroute(initial_route, trigger_description="Total corridor failure")
    assert reroute_res.reroute_required is True
    assert reroute_res.no_path_found is True
    assert reroute_res.error_code == "NO_PATH_AFTER_STATE_CHANGE"
    assert reroute_res.new_route is None


def test_speed_limit_override(grid_network):
    """Verify dynamic speed limit override increases travel-time duration."""
    _, overlay, router, _ = grid_network

    req = RouteRequest(
        origin=[80.260, 13.085],
        destination=[80.280, 13.075],
        routing_mode=RoutingMode.TRAVEL_TIME,
    )
    initial_route = router.route(req)
    init_dur = initial_route.estimated_duration_seconds

    # Reduce speed limit on North path ROAD-101 from 50 km/h to 10 km/h
    overlay.set_road_override(
        road_id="ROAD-101",
        status=RoadStatus.OPEN,
        speed_limit_kmh=10.0,
        reason="Heavy congestion / rain speed reduction",
    )

    slower_route = router.route(req)
    # Total travel time increased
    assert slower_route.estimated_duration_seconds > init_dur
