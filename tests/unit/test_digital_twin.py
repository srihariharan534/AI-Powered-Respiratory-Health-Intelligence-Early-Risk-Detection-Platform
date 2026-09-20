"""
Tests for NEXUS Digital Twin - Emergency Operational State Authority.
Validates:
- Entity registration and queries
- State transitions (Road, Bridge, Hospital, Shelter, Incident, Flood, Vulnerability)
- Capacity validation (0 <= available <= capacity)
- State versioning and determinism
- Event idempotency
- In-memory immutable event history
- Bridge failure to Road causal propagation
- State snapshot and deterministic event replay
- Tight Phase 08 Dynamic Rerouting overlay integration
- End-to-end bridge failure -> road closure -> dynamic rerouting
"""

from datetime import datetime, timezone

import pytest

from digital_twin.entities import (
    BridgeEntity,
    FloodZoneEntity,
    HospitalEntity,
    IncidentEntity,
    PopulationEntity,
    RescueTeamEntity,
    RescueTeamStatus,
    RoadEntity,
    ShelterEntity,
    VulnerabilityCategory,
    VulnerableGroupEntity,
)
from digital_twin.entities.bridge import BridgeStatus
from digital_twin.entities.flood_zone import FloodSeverity
from digital_twin.events import (
    BridgeStatusChangedEvent,
    CapacityUpdatedEvent,
    EventSource,
    FloodUpdatedEvent,
    IncidentCreatedEvent,
    RoadStatusChangedEvent,
    VulnerabilityUpdatedEvent,
)
from digital_twin.state.state_manager import (
    DigitalTwinStateManager,
)
from geospatial.routing import DynamicRerouter
from geospatial.routing.state_overlay import StateOverlay
from services.api.app.schemas.hospital import HospitalStatus
from services.api.app.schemas.incident import IncidentSeverity, IncidentStatus
from services.api.app.schemas.road import Accessibility, RoadStatus
from services.api.app.schemas.shelter import ShelterStatus


@pytest.fixture
def twin_manager() -> DigitalTwinStateManager:
    """Fixture providing a fresh Digital Twin state manager."""
    return DigitalTwinStateManager()


@pytest.fixture
def synthetic_twin_fixture(twin_manager: DigitalTwinStateManager) -> DigitalTwinStateManager:
    """
    Creates a deterministic synthetic test fixture containing:
    Road R-001, Bridge B-001, Hospital H-001, Shelter S-001,
    Rescue Team T-001, Incident I-001, Flood Zone F-001,
    Population P-001, Vulnerable Group V-001.
    """
    now = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Road R-001
    twin_manager.register_road(RoadEntity(
        road_id="R-001",
        name="Main Coastal Highway",
        status=RoadStatus.OPEN,
        accessibility=Accessibility.ALL_VEHICLES,
        speed_kmh=60.0,
        associated_bridge_ids=["B-001"],
        updated_at=now,
        source="TEST_FIXTURE",
    ))

    # 2. Bridge B-001 (associated with Road R-001)
    twin_manager.register_bridge(BridgeEntity(
        bridge_id="B-001",
        name="Mahanadi Causeway Bridge",
        road_id="R-001",
        status=BridgeStatus.OPEN,
        clearance_m=5.5,
        updated_at=now,
        source="TEST_FIXTURE",
    ))

    # 3. Hospital H-001
    twin_manager.register_hospital(HospitalEntity(
        hospital_id="H-001",
        name="District Central Hospital",
        capacity=200,
        available_capacity=50,
        emergency_available=True,
        icu_available=10,
        status=HospitalStatus.OPERATIONAL,
        location={"type": "Point", "coordinates": [85.83, 20.30]},
        updated_at=now,
        source="TEST_FIXTURE",
    ))

    # 4. Shelter S-001
    twin_manager.register_shelter(ShelterEntity(
        shelter_id="S-001",
        name="Cyclone Relief Shelter A",
        capacity=500,
        available_capacity=350,
        status=ShelterStatus.OPEN,
        location={"type": "Point", "coordinates": [85.84, 20.31]},
        updated_at=now,
        source="TEST_FIXTURE",
    ))

    # 5. Rescue Team T-001
    twin_manager.register_rescue_team(RescueTeamEntity(
        rescue_team_id="T-001",
        name="ODRAF Unit 3",
        status=RescueTeamStatus.AVAILABLE,
        location={"type": "Point", "coordinates": [85.82, 20.29]},
        vehicle_type="4X4",
        capacity=6,
        updated_at=now,
        source="TEST_FIXTURE",
    ))

    # 6. Incident I-001
    twin_manager.register_incident(IncidentEntity(
        incident_id="I-001",
        event_type="FLOOD_STRANDED",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        location={"type": "Point", "coordinates": [85.85, 20.32]},
        reported_at=now,
        description="Stranded villagers near canal bank",
        source="TEST_FIXTURE",
        priority=1,
        updated_at=now,
    ))

    # 7. Flood Zone F-001
    twin_manager.register_flood_zone(FloodZoneEntity(
        flood_zone_id="F-001",
        name="Kushabhadra Sector 4",
        geometry={
            "type": "Polygon",
            "coordinates": [[[85.80, 20.25], [85.85, 20.25], [85.85, 20.30], [85.80, 20.30], [85.80, 20.25]]],
        },
        severity=FloodSeverity.MODERATE,
        water_depth_m=0.75,
        updated_at=now,
        source="TEST_FIXTURE",
    ))

    # 8. Population P-001
    twin_manager.register_population(PopulationEntity(
        population_id="P-001",
        count=12500,
        location={"type": "Point", "coordinates": [85.82, 20.28]},
        updated_at=now,
        source="TEST_FIXTURE",
    ))

    # 9. Vulnerable Group V-001
    twin_manager.register_vulnerable_group(VulnerableGroupEntity(
        vulnerable_group_id="V-001",
        name="Elderly Care Home Residents",
        category=VulnerabilityCategory.ELDERLY,
        count=45,
        location={"type": "Point", "coordinates": [85.83, 20.29]},
        updated_at=now,
        source="TEST_FIXTURE",
    ))

    return twin_manager


class TestDigitalTwinEntities:
    """Test entity registration and typed query interfaces."""

    def test_synthetic_fixture_entities_registered(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        assert tm.get_road("R-001") is not None
        assert tm.get_bridge("B-001") is not None
        assert tm.get_hospital("H-001") is not None
        assert tm.get_shelter("S-001") is not None
        assert tm.get_rescue_team("T-001") is not None
        assert tm.get_incident("I-001") is not None
        assert tm.get_flood_zone("F-001") is not None
        assert tm.get_population("P-001") is not None
        assert tm.get_vulnerable_group("V-001") is not None

    def test_list_entities_types(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        roads = tm.list_entities("roads")
        assert len(roads) == 1
        assert roads[0].road_id == "R-001"

        hospitals = tm.list_entities("hospitals")
        assert len(hospitals) == 1
        assert hospitals[0].hospital_id == "H-001"

    def test_entity_immutability_through_queries(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        road = tm.get_road("R-001")
        assert road is not None
        road.status = RoadStatus.BLOCKED  # Mutating queried copy

        # The internal state must remain unchanged
        road_internal = tm.get_road("R-001")
        assert road_internal is not None
        assert road_internal.status == RoadStatus.OPEN


class TestStateTransitionsAndVersioning:
    """Test transitions, version increments, and validation."""

    def test_road_status_transition_increments_version(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        assert tm.state_version == 0

        evt = RoadStatusChangedEvent(
            event_id="EVT-001",
            road_id="R-001",
            new_status=RoadStatus.BLOCKED,
            source=EventSource.FIELD_REPORT,
            reason="Downed power lines and standing water",
        )
        res = tm.apply_event(evt)
        assert res.applied is True
        assert tm.state_version == 1

        road = tm.get_road("R-001")
        assert road is not None
        assert road.status == RoadStatus.BLOCKED
        assert road.reason == "Downed power lines and standing water"

    def test_capacity_validation_rules(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture

        # Valid capacity update
        valid_evt = CapacityUpdatedEvent(
            event_id="EVT-CAP-001",
            facility_type="HOSPITAL",
            facility_id="H-001",
            capacity=200,
            available_capacity=20,
            icu_available=2,
            source=EventSource.COMMAND_CENTER,
        )
        res = tm.apply_event(valid_evt)
        assert res.applied is True
        hosp = tm.get_hospital("H-001")
        assert hosp is not None
        assert hosp.available_capacity == 20

        # Invalid capacity: available_capacity > capacity must raise ValueError at schema level
        with pytest.raises(ValueError, match="cannot exceed total capacity"):
            CapacityUpdatedEvent(
                event_id="EVT-CAP-INVALID",
                facility_type="HOSPITAL",
                facility_id="H-001",
                capacity=100,
                available_capacity=150,
            )

    def test_flood_unknown_depth_distinguishable_from_zero(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        evt = FloodUpdatedEvent(
            event_id="EVT-FLOOD-001",
            flood_zone_id="F-001",
            geometry={"type": "Polygon", "coordinates": []},
            severity=FloodSeverity.SEVERE,
            water_depth_m=None,  # Unknown depth
            source=EventSource.SIMULATION,
        )
        res = tm.apply_event(evt)
        assert res.applied is True
        fz = tm.get_flood_zone("F-001")
        assert fz is not None
        assert fz.water_depth_m is None
        assert fz.water_depth_m != 0.0

    def test_vulnerability_update_without_scoring(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        evt = VulnerabilityUpdatedEvent(
            event_id="EVT-VG-001",
            vulnerable_group_id="V-001",
            category=VulnerabilityCategory.HEALTHCARE,
            count=60,
            source=EventSource.FIELD_REPORT,
        )
        res = tm.apply_event(evt)
        assert res.applied is True
        vg = tm.get_vulnerable_group("V-001")
        assert vg is not None
        assert vg.count == 60
        assert vg.category == VulnerabilityCategory.HEALTHCARE


class TestIdempotencyAndNoOps:
    """Test duplicate detection and no-op handling."""

    def test_idempotency_same_event_applied_twice(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        evt = RoadStatusChangedEvent(
            event_id="EVT-IDEMPOTENT-001",
            road_id="R-001",
            new_status=RoadStatus.RESTRICTED,
            source=EventSource.FIELD_REPORT,
        )
        res1 = tm.apply_event(evt)
        assert res1.applied is True
        v1 = tm.state_version

        # Apply exact same event again
        res2 = tm.apply_event(evt)
        assert res2.applied is False
        assert res2.is_duplicate is True
        assert tm.state_version == v1  # Version did NOT increment
        assert len(tm.get_events()) == 1  # Not duplicated in history

    def test_no_op_event_handling(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        # Road is already OPEN
        evt = RoadStatusChangedEvent(
            event_id="EVT-NOOP-001",
            road_id="R-001",
            new_status=RoadStatus.OPEN,
            source=EventSource.SYSTEM,
        )
        res = tm.apply_event(evt)
        assert res.applied is False
        assert res.is_no_op is True
        assert tm.state_version == 0  # No increment for no-op


class TestBridgeFailurePropagation:
    """Test bridge failure cascading to associated road entity."""

    def test_bridge_failure_cascades_to_road(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        assert tm.get_road("R-001").status == RoadStatus.OPEN

        evt = BridgeStatusChangedEvent(
            event_id="EVT-BRIDGE-001",
            bridge_id="B-001",
            new_status=BridgeStatus.BLOCKED,
            propagate_to_road=True,
            source=EventSource.SIMULATION,
            reason="DEMO: Bridge submerged by surge",
        )
        res = tm.apply_event(evt)
        assert res.applied is True
        assert len(res.cascaded_event_ids) == 1

        # Check bridge state
        bridge = tm.get_bridge("B-001")
        assert bridge is not None
        assert bridge.status == BridgeStatus.BLOCKED

        # Check causally propagated road state
        road = tm.get_road("R-001")
        assert road is not None
        assert road.status == RoadStatus.BLOCKED
        assert "Bridge B-001" in (road.reason or "")

        # Verify causality in event log
        events = tm.get_events()
        assert len(events) == 2
        bridge_evt = events[0]
        road_evt = events[1]
        assert road_evt.caused_by_event_id == bridge_evt.event_id


class TestSnapshotsAndReplay:
    """Test state snapshots and deterministic event replay."""

    def test_snapshot_and_replay_identity(self, synthetic_twin_fixture: DigitalTwinStateManager):
        tm = synthetic_twin_fixture
        initial_snapshot = tm.create_snapshot()

        events = [
            RoadStatusChangedEvent(
                event_id="EVT-SEQ-1",
                road_id="R-001",
                new_status=RoadStatus.RESTRICTED,
                source=EventSource.FIELD_REPORT,
            ),
            CapacityUpdatedEvent(
                event_id="EVT-SEQ-2",
                facility_type="HOSPITAL",
                facility_id="H-001",
                capacity=200,
                available_capacity=10,
                source=EventSource.COMMAND_CENTER,
            ),
            IncidentCreatedEvent(
                event_id="EVT-SEQ-3",
                incident_id="I-002",
                incident_type="MEDICAL_EMERGENCY",
                severity=IncidentSeverity.CRITICAL,
                location={"type": "Point", "coordinates": [85.83, 20.30]},
                source=EventSource.FIELD_REPORT,
            ),
        ]

        # Apply sequentially to live manager
        for evt in events:
            tm.apply_event(evt)

        final_live_version = tm.state_version
        final_live_road = tm.get_road("R-001")
        final_live_hosp = tm.get_hospital("H-001")
        final_live_incident = tm.get_incident("I-002")

        # Deterministic Replay from initial snapshot
        replayed_manager = DigitalTwinStateManager.replay(initial_snapshot, events)

        assert replayed_manager.state_version == final_live_version
        assert replayed_manager.get_road("R-001") == final_live_road
        assert replayed_manager.get_hospital("H-001") == final_live_hosp
        assert replayed_manager.get_incident("I-002") == final_live_incident


class TestPhase08RoutingIntegration:
    """
    End-to-End Integration Test:
    1. Create initial road network and route through Bridge B-102 / Road ROAD-102.
    2. Attach Phase 08 StateOverlay to Digital Twin.
    3. Calculate initial route traversing Road ROAD-102.
    4. Digital Twin receives BridgeStatusChangedEvent (BLOCKED) for Bridge B-102.
    5. Bridge failure propagates to Road ROAD-102 in Digital Twin.
    6. Digital Twin version increments.
    7. Routing state overlay receives the update synchronously.
    8. DynamicRerouter detects route invalidation and recalculates new route avoiding ROAD-102.
    """

    def test_digital_twin_bridge_failure_triggers_rerouting(self):
        import networkx as nx

        from geospatial.routing import (
            EmergencyRouter,
            RouteRequest,
            RoutingGraphAdapter,
            RoutingMode,
        )

        G = nx.MultiDiGraph(id="grid-network")
        overlay = StateOverlay()

        nodes = {
            "NODE-A": (80.260, 13.085),
            "NODE-B": (80.270, 13.085),
            "NODE-C": (80.280, 13.085),
            "NODE-D": (80.260, 13.075),
            "NODE-E": (80.270, 13.075),
            "NODE-F": (80.280, 13.075),
        }
        for n, (lon, lat) in nodes.items():
            G.add_node(n, longitude=lon, latitude=lat)

        def add_bi_edge(u, v, way_id, length_m, speed_kmh=50.0, is_bridge=False, bridge_id=None):
            u_pt = nodes[u]
            v_pt = nodes[v]
            e_fwd = f"EDGE-{way_id}-{u}-{v}"
            e_rev = f"EDGE-{way_id}-{v}-{u}"
            road_id = f"ROAD-{way_id}"
            fwd_data = {
                "edge_id": e_fwd, "road_id": road_id, "source_node": u, "target_node": v,
                "length_meters": length_m, "road_type": "primary", "accessibility": "ALL_VEHICLES",
                "speed_limit_kmh": speed_kmh, "is_bridge": is_bridge, "bridge_id": bridge_id,
                "geometry": [[u_pt[0], u_pt[1]], [v_pt[0], v_pt[1]]], "status": "OPEN",
            }
            rev_data = {
                "edge_id": e_rev, "road_id": road_id, "source_node": v, "target_node": u,
                "length_meters": length_m, "road_type": "primary", "accessibility": "ALL_VEHICLES",
                "speed_limit_kmh": speed_kmh, "is_bridge": is_bridge, "bridge_id": bridge_id,
                "geometry": [[v_pt[0], v_pt[1]], [u_pt[0], u_pt[1]]], "status": "OPEN",
            }
            G.add_edge(u, v, key=e_fwd, **fwd_data)
            G.add_edge(v, u, key=e_rev, **rev_data)
            overlay.register_road_edge(road_id, e_fwd, bridge_id)
            overlay.register_road_edge(road_id, e_rev, bridge_id)

        # North path: A -> B -> C -> F (3000m)
        add_bi_edge("NODE-A", "NODE-B", "101", 1000.0)
        add_bi_edge("NODE-B", "NODE-C", "102", 1000.0, is_bridge=True, bridge_id="BRIDGE-102")
        add_bi_edge("NODE-C", "NODE-F", "104", 1000.0)

        # South bypass path: A -> D -> E -> F (3300m)
        add_bi_edge("NODE-A", "NODE-D", "103", 1100.0)
        add_bi_edge("NODE-D", "NODE-E", "105", 1100.0)
        add_bi_edge("NODE-E", "NODE-F", "107", 1100.0)

        adapter = RoutingGraphAdapter(G, overlay=overlay)
        router = EmergencyRouter(adapter)
        rerouter = DynamicRerouter(router, overlay)

        # Initialize Digital Twin State Manager with attached overlay
        twin = DigitalTwinStateManager(routing_overlay=overlay)
        twin.register_road(RoadEntity(
            road_id="ROAD-102",
            status=RoadStatus.OPEN,
            associated_bridge_ids=["BRIDGE-102"],
            source="TEST_FIXTURE",
        ))
        twin.register_bridge(BridgeEntity(
            bridge_id="BRIDGE-102",
            road_id="ROAD-102",
            status=BridgeStatus.OPEN,
            source="TEST_FIXTURE",
        ))

        # Initial baseline route calculation: chooses shorter North path
        req = RouteRequest(
            origin=[80.260, 13.085],
            destination=[80.280, 13.075],
            routing_mode=RoutingMode.DISTANCE,
        )
        initial_route = router.route(req)
        assert initial_route.path_nodes == ["NODE-A", "NODE-B", "NODE-C", "NODE-F"]
        assert "EDGE-102-NODE-B-NODE-C" in initial_route.path_edges

        # Digital Twin receives simulated Bridge Failure event
        bridge_event = BridgeStatusChangedEvent(
            event_id="EVT-SIM-B102-FAIL",
            bridge_id="BRIDGE-102",
            new_status=BridgeStatus.BLOCKED,
            propagate_to_road=True,
            source=EventSource.SIMULATION,
            reason="DEMO: Flash flood overtopped causeway bridge",
        )
        res = twin.apply_event(bridge_event)
        assert res.applied is True

        # Verify Digital Twin updated both Bridge and Road operational state
        assert twin.get_bridge("BRIDGE-102").status == BridgeStatus.BLOCKED
        assert twin.get_road("ROAD-102").status == RoadStatus.BLOCKED
        assert twin.state_version >= 1

        # Evaluate and trigger dynamic rerouting with Phase 08
        reroute_res = rerouter.evaluate_and_reroute(
            current_route=initial_route,
            trigger_description="Digital Twin Bridge Failure propagation",
        )
        assert reroute_res.reroute_required is True
        assert reroute_res.new_route is not None
        # Must have diverted to South corridor: A -> D -> E -> F
        assert reroute_res.new_route.path_nodes == ["NODE-A", "NODE-D", "NODE-E", "NODE-F"]
        assert "EDGE-102-NODE-B-NODE-C" not in reroute_res.new_route.path_edges
        assert reroute_res.comparison.route_changed is True
        assert "ROAD-102" in reroute_res.explanation.affected_roads

