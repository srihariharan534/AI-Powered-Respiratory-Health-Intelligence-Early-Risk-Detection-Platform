"""
NEXUS Digital Twin - State Manager.
Authoritative, versioned operational state authority for the emergency environment.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar

from pydantic import BaseModel, Field

from digital_twin.entities.bridge import BridgeEntity, BridgeStatus
from digital_twin.entities.flood_zone import FloodZoneEntity
from digital_twin.entities.hospital import HospitalEntity
from digital_twin.entities.incident import IncidentEntity
from digital_twin.entities.population import PopulationEntity
from digital_twin.entities.rescue_team import RescueTeamEntity
from digital_twin.entities.road import RoadEntity
from digital_twin.entities.shelter import ShelterEntity
from digital_twin.entities.vulnerable_group import VulnerableGroupEntity
from digital_twin.events.base import TwinEvent
from digital_twin.events.capacity_updated import CapacityUpdatedEvent
from digital_twin.events.facility_status_changed import FacilityStatusChangedEvent
from digital_twin.events.flood_updated import FloodUpdatedEvent
from digital_twin.events.incident_created import (
    IncidentCreatedEvent,
    IncidentStatusChangedEvent,
)
from digital_twin.events.road_status_changed import (
    BridgeStatusChangedEvent,
    RoadStatusChangedEvent,
)
from digital_twin.events.vulnerability_updated import (
    PopulationUpdatedEvent,
    VulnerabilityUpdatedEvent,
)
from digital_twin.state.transitions import (
    StateTransitionError,
    apply_bridge_status_transition,
    apply_facility_status_transition,
    apply_flood_transition,
    apply_hospital_capacity_transition,
    apply_incident_status_transition,
    apply_population_transition,
    apply_road_status_transition,
    apply_shelter_capacity_transition,
    apply_vulnerability_transition,
)

from geospatial.routing.dynamic_state import OverrideSource
from geospatial.routing.state_overlay import StateOverlay
from services.api.app.schemas.road import Accessibility, RoadStatus

logger = logging.getLogger("nexus.digital_twin.state")

T = TypeVar("T", bound=BaseModel)


class TwinSnapshot(BaseModel):
    """
    Deterministic point-in-time state snapshot of the Digital Twin.
    """
    state_version: int = Field(..., description="Monotonically increasing state version")
    timestamp: datetime = Field(..., description="UTC timestamp when snapshot was captured")
    roads: Dict[str, RoadEntity] = Field(default_factory=dict)
    bridges: Dict[str, BridgeEntity] = Field(default_factory=dict)
    hospitals: Dict[str, HospitalEntity] = Field(default_factory=dict)
    shelters: Dict[str, ShelterEntity] = Field(default_factory=dict)
    rescue_teams: Dict[str, RescueTeamEntity] = Field(default_factory=dict)
    incidents: Dict[str, IncidentEntity] = Field(default_factory=dict)
    flood_zones: Dict[str, FloodZoneEntity] = Field(default_factory=dict)
    populations: Dict[str, PopulationEntity] = Field(default_factory=dict)
    vulnerable_groups: Dict[str, VulnerableGroupEntity] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
    }


class TransitionResult(BaseModel):
    """
    Result returned after evaluating and applying an event.
    """
    event_id: str
    applied: bool
    state_version: int
    is_duplicate: bool = False
    is_no_op: bool = False
    message: str = ""
    cascaded_event_ids: List[str] = Field(default_factory=list)


class DigitalTwinStateManager:
    """
    Authoritative Digital Twin Operational State Authority.
    - Maintains coherent, strongly typed, versioned state of emergency entities.
    - Enforces idempotency via immutable event IDs.
    - Maintains an append-only in-memory event audit log.
    - Synchronously coordinates with Phase 08 StateOverlay for zero-conflict road operational state.
    """

    def __init__(
        self,
        routing_overlay: Optional[StateOverlay] = None,
        initial_version: int = 0,
    ) -> None:
        self._version: int = initial_version
        self._updated_at: datetime = datetime.now(timezone.utc)

        # Entity Registries (stable_id -> Entity)
        self._roads: Dict[str, RoadEntity] = {}
        self._bridges: Dict[str, BridgeEntity] = {}
        self._hospitals: Dict[str, HospitalEntity] = {}
        self._shelters: Dict[str, ShelterEntity] = {}
        self._rescue_teams: Dict[str, RescueTeamEntity] = {}
        self._incidents: Dict[str, IncidentEntity] = {}
        self._flood_zones: Dict[str, FloodZoneEntity] = {}
        self._populations: Dict[str, PopulationEntity] = {}
        self._vulnerable_groups: Dict[str, VulnerableGroupEntity] = {}

        # Append-only audit log of successfully applied non-duplicate events
        self._event_log: List[TwinEvent] = []
        # Fast lookup set of seen event_ids for idempotency
        self._seen_event_ids: Dict[str, int] = {}  # event_id -> state_version when applied

        # Phase 08 Routing State Overlay integration
        self._routing_overlay: Optional[StateOverlay] = routing_overlay

    @property
    def state_version(self) -> int:
        """Current operational state version."""
        return self._version

    @property
    def updated_at(self) -> datetime:
        """Timestamp of last state modification."""
        return self._updated_at

    @property
    def routing_overlay(self) -> Optional[StateOverlay]:
        return self._routing_overlay

    def set_routing_overlay(self, overlay: StateOverlay) -> None:
        """Attach or update the Phase 08 routing state overlay."""
        self._routing_overlay = overlay
        self._sync_all_roads_to_overlay()

    # -------------------------------------------------------------------------
    # Entity Registration (Initial Setup / Ingestion)
    # -------------------------------------------------------------------------

    def register_road(self, road: RoadEntity) -> None:
        """Register a road segment entity."""
        self._roads[road.road_id] = road.model_copy(deep=True)
        if self._routing_overlay is not None:
            self._sync_road_to_overlay(road)

    def register_bridge(self, bridge: BridgeEntity) -> None:
        """Register a bridge entity."""
        self._bridges[bridge.bridge_id] = bridge.model_copy(deep=True)
        if self._routing_overlay is not None:
            self._sync_bridge_to_overlay(bridge)

    def register_hospital(self, hospital: HospitalEntity) -> None:
        """Register a hospital facility entity."""
        self._hospitals[hospital.hospital_id] = hospital.model_copy(deep=True)

    def register_shelter(self, shelter: ShelterEntity) -> None:
        """Register a shelter entity."""
        self._shelters[shelter.shelter_id] = shelter.model_copy(deep=True)

    def register_rescue_team(self, team: RescueTeamEntity) -> None:
        """Register a rescue team entity."""
        self._rescue_teams[team.rescue_team_id] = team.model_copy(deep=True)

    def register_incident(self, incident: IncidentEntity) -> None:
        """Register an emergency incident entity."""
        self._incidents[incident.incident_id] = incident.model_copy(deep=True)

    def register_flood_zone(self, flood_zone: FloodZoneEntity) -> None:
        """Register a flood zone entity."""
        self._flood_zones[flood_zone.flood_zone_id] = flood_zone.model_copy(deep=True)

    def register_population(self, population: PopulationEntity) -> None:
        """Register a population unit entity."""
        self._populations[population.population_id] = population.model_copy(deep=True)

    def register_vulnerable_group(self, vg: VulnerableGroupEntity) -> None:
        """Register a vulnerable group entity."""
        self._vulnerable_groups[vg.vulnerable_group_id] = vg.model_copy(deep=True)

    # -------------------------------------------------------------------------
    # Entity Queries
    # -------------------------------------------------------------------------

    def get_road(self, road_id: str) -> Optional[RoadEntity]:
        entity = self._roads.get(road_id)
        return entity.model_copy(deep=True) if entity else None

    def get_bridge(self, bridge_id: str) -> Optional[BridgeEntity]:
        entity = self._bridges.get(bridge_id)
        return entity.model_copy(deep=True) if entity else None

    def get_hospital(self, hospital_id: str) -> Optional[HospitalEntity]:
        entity = self._hospitals.get(hospital_id)
        return entity.model_copy(deep=True) if entity else None

    def get_shelter(self, shelter_id: str) -> Optional[ShelterEntity]:
        entity = self._shelters.get(shelter_id)
        return entity.model_copy(deep=True) if entity else None

    def get_rescue_team(self, team_id: str) -> Optional[RescueTeamEntity]:
        entity = self._rescue_teams.get(team_id)
        return entity.model_copy(deep=True) if entity else None

    def get_incident(self, incident_id: str) -> Optional[IncidentEntity]:
        entity = self._incidents.get(incident_id)
        return entity.model_copy(deep=True) if entity else None

    def get_flood_zone(self, flood_zone_id: str) -> Optional[FloodZoneEntity]:
        entity = self._flood_zones.get(flood_zone_id)
        return entity.model_copy(deep=True) if entity else None

    def get_population(self, population_id: str) -> Optional[PopulationEntity]:
        entity = self._populations.get(population_id)
        return entity.model_copy(deep=True) if entity else None

    def get_vulnerable_group(self, vg_id: str) -> Optional[VulnerableGroupEntity]:
        entity = self._vulnerable_groups.get(vg_id)
        return entity.model_copy(deep=True) if entity else None

    def list_entities(self, entity_type: str) -> List[Any]:
        """
        List all entities of a given type.
        entity_type: 'roads', 'bridges', 'hospitals', 'shelters', 'rescue_teams',
                     'incidents', 'flood_zones', 'populations', 'vulnerable_groups'.
        """
        registry_map = {
            "roads": self._roads,
            "bridges": self._bridges,
            "hospitals": self._hospitals,
            "shelters": self._shelters,
            "rescue_teams": self._rescue_teams,
            "incidents": self._incidents,
            "flood_zones": self._flood_zones,
            "populations": self._populations,
            "vulnerable_groups": self._vulnerable_groups,
        }
        target = registry_map.get(entity_type.lower())
        if target is None:
            raise KeyError(f"Unknown entity type: '{entity_type}'. Valid types: {list(registry_map.keys())}")
        return [item.model_copy(deep=True) for item in target.values()]

    # -------------------------------------------------------------------------
    # Event History & Audit
    # -------------------------------------------------------------------------

    def get_event(self, event_id: str) -> Optional[TwinEvent]:
        for evt in self._event_log:
            if evt.event_id == event_id:
                return evt
        return None

    def get_events(
        self,
        event_type: Optional[str] = None,
        since_version: Optional[int] = None,
    ) -> List[TwinEvent]:
        """Query immutable event history with optional filters."""
        results = []
        for evt in self._event_log:
            if event_type and evt.event_type != event_type:
                continue
            if since_version is not None and evt.metadata.get("state_version", 0) <= since_version:
                continue
            results.append(evt)
        return results

    # -------------------------------------------------------------------------
    # Event Application & State Transitions
    # -------------------------------------------------------------------------

    def apply_event(self, event: TwinEvent) -> TransitionResult:
        """
        Apply a domain event to the Digital Twin:
        1. Check idempotency (duplicate event_id is rejected as no-op).
        2. Validate event and target entity state.
        3. Transition entity state.
        4. If state changed:
           - Increment state_version.
           - Sync with Phase 08 routing overlay if road/bridge affected.
           - Record in append-only event log.
        5. If bridge failed and propagation enabled, causally propagate to associated road.
        """
        # 1. Idempotency Check
        if event.event_id in self._seen_event_ids:
            return TransitionResult(
                event_id=event.event_id,
                applied=False,
                state_version=self._version,
                is_duplicate=True,
                message=f"Duplicate event {event.event_id}; already applied at version {self._seen_event_ids[event.event_id]}",
            )

        # 2. Dispatch by Event Type
        if isinstance(event, RoadStatusChangedEvent):
            res = self._handle_road_status_changed(event)
        elif isinstance(event, BridgeStatusChangedEvent):
            res = self._handle_bridge_status_changed(event)
        elif isinstance(event, CapacityUpdatedEvent):
            res = self._handle_capacity_updated(event)
        elif isinstance(event, FacilityStatusChangedEvent):
            res = self._handle_facility_status_changed(event)
        elif isinstance(event, IncidentCreatedEvent):
            res = self._handle_incident_created(event)

        elif isinstance(event, IncidentStatusChangedEvent):
            res = self._handle_incident_status_changed(event)
        elif isinstance(event, FloodUpdatedEvent):
            res = self._handle_flood_updated(event)
        elif isinstance(event, VulnerabilityUpdatedEvent):
            res = self._handle_vulnerability_updated(event)
        elif isinstance(event, PopulationUpdatedEvent):
            res = self._handle_population_updated(event)
        else:
            raise StateTransitionError(f"Unsupported event type: {type(event)}")

        return res

    def _handle_road_status_changed(self, event: RoadStatusChangedEvent) -> TransitionResult:
        entity = self._roads.get(event.road_id)
        if entity is None:
            # Auto-create road entity if not yet registered
            entity = RoadEntity(
                road_id=event.road_id,
                status=RoadStatus.OPEN,
                accessibility=Accessibility.ALL_VEHICLES,
            )
            self._roads[event.road_id] = entity

        updated_entity, is_no_op = apply_road_status_transition(entity, event)

        if is_no_op:
            self._seen_event_ids[event.event_id] = self._version
            return TransitionResult(
                event_id=event.event_id,
                applied=False,
                state_version=self._version,
                is_no_op=True,
                message="Event resulted in no operational state change",
            )

        self._roads[event.road_id] = updated_entity
        self._commit_event(event)

        # Synchronously update Phase 08 routing overlay
        if self._routing_overlay is not None:
            self._sync_road_to_overlay(updated_entity)

        return TransitionResult(
            event_id=event.event_id,
            applied=True,
            state_version=self._version,
            message=f"Road {event.road_id} transitioned to {event.new_status.value}",
        )

    def _handle_bridge_status_changed(self, event: BridgeStatusChangedEvent) -> TransitionResult:
        entity = self._bridges.get(event.bridge_id)
        if entity is None:
            entity = BridgeEntity(
                bridge_id=event.bridge_id,
                status=BridgeStatus.OPEN,
            )
            self._bridges[event.bridge_id] = entity

        updated_entity, is_no_op = apply_bridge_status_transition(entity, event)

        if is_no_op:
            self._seen_event_ids[event.event_id] = self._version
            return TransitionResult(
                event_id=event.event_id,
                applied=False,
                state_version=self._version,
                is_no_op=True,
                message="Bridge event resulted in no operational state change",
            )

        self._bridges[event.bridge_id] = updated_entity
        self._commit_event(event)

        if self._routing_overlay is not None:
            self._sync_bridge_to_overlay(updated_entity)

        cascaded_ids: List[str] = []

        # Bridge -> Road causal propagation
        if event.propagate_to_road and updated_entity.road_id:
            road_id = updated_entity.road_id
            target_road_status = RoadStatus.OPEN
            if event.new_status in (BridgeStatus.BLOCKED, BridgeStatus.COLLAPSED, BridgeStatus.CLOSED):
                target_road_status = RoadStatus.BLOCKED
            elif event.new_status in (BridgeStatus.RESTRICTED, BridgeStatus.SUBMERGED):
                target_road_status = RoadStatus.RESTRICTED

            cascaded_evt_id = f"CAUSED-{event.event_id}-{road_id}"
            cascaded_evt = RoadStatusChangedEvent(
                event_id=cascaded_evt_id,
                road_id=road_id,
                new_status=target_road_status,
                source=event.source,
                reason=f"Cascading closure caused by Bridge {event.bridge_id} status {event.new_status.value}",
                caused_by_event_id=event.event_id,
                timestamp=event.timestamp,
            )
            cascade_res = self.apply_event(cascaded_evt)
            if cascade_res.applied:
                cascaded_ids.append(cascaded_evt_id)

        return TransitionResult(
            event_id=event.event_id,
            applied=True,
            state_version=self._version,
            message=f"Bridge {event.bridge_id} transitioned to {event.new_status.value}",
            cascaded_event_ids=cascaded_ids,
        )

    def _handle_capacity_updated(self, event: CapacityUpdatedEvent) -> TransitionResult:
        if event.facility_type.upper() == "HOSPITAL":
            hospital = self._hospitals.get(event.facility_id)
            if hospital is None:
                raise StateTransitionError(f"Hospital {event.facility_id} not registered")
            updated, is_no_op = apply_hospital_capacity_transition(hospital, event)
            if is_no_op:
                self._seen_event_ids[event.event_id] = self._version
                return TransitionResult(event_id=event.event_id, applied=False, state_version=self._version, is_no_op=True)
            self._hospitals[event.facility_id] = updated
        elif event.facility_type.upper() == "SHELTER":
            shelter = self._shelters.get(event.facility_id)
            if shelter is None:
                raise StateTransitionError(f"Shelter {event.facility_id} not registered")
            updated, is_no_op = apply_shelter_capacity_transition(shelter, event)
            if is_no_op:
                self._seen_event_ids[event.event_id] = self._version
                return TransitionResult(event_id=event.event_id, applied=False, state_version=self._version, is_no_op=True)
            self._shelters[event.facility_id] = updated
        else:
            raise StateTransitionError(f"Unknown facility type '{event.facility_type}' for capacity update")

        self._commit_event(event)
        return TransitionResult(
            event_id=event.event_id,
            applied=True,
            state_version=self._version,
            message=f"Facility {event.facility_id} capacity updated",
        )

    def _handle_facility_status_changed(self, event: FacilityStatusChangedEvent) -> TransitionResult:
        if event.facility_type.upper() == "HOSPITAL":
            hospital = self._hospitals.get(event.facility_id)
            if hospital is None:
                raise StateTransitionError(f"Hospital {event.facility_id} not registered")
            updated, is_no_op = apply_facility_status_transition(hospital, event)
            if is_no_op:
                self._seen_event_ids[event.event_id] = self._version
                return TransitionResult(event_id=event.event_id, applied=False, state_version=self._version, is_no_op=True)
            self._hospitals[event.facility_id] = updated
        elif event.facility_type.upper() == "SHELTER":
            shelter = self._shelters.get(event.facility_id)
            if shelter is None:
                raise StateTransitionError(f"Shelter {event.facility_id} not registered")
            updated, is_no_op = apply_facility_status_transition(shelter, event)
            if is_no_op:
                self._seen_event_ids[event.event_id] = self._version
                return TransitionResult(event_id=event.event_id, applied=False, state_version=self._version, is_no_op=True)
            self._shelters[event.facility_id] = updated
        else:
            raise StateTransitionError(f"Unknown facility type '{event.facility_type}' for status change")

        self._commit_event(event)
        return TransitionResult(
            event_id=event.event_id,
            applied=True,
            state_version=self._version,
            message=f"Facility {event.facility_id} status updated to {event.new_status}",
        )

    def _handle_incident_created(self, event: IncidentCreatedEvent) -> TransitionResult:

        incident = IncidentEntity(
            incident_id=event.incident_id,
            event_type=event.incident_type,
            severity=event.severity,
            status=event.status,
            location=event.location,
            reported_at=event.timestamp,
            reported_by=event.reported_by,
            description=event.description,
            evidence=event.evidence,
            source=event.source.value,
            priority=event.priority,
            updated_at=event.timestamp,
        )
        self._incidents[event.incident_id] = incident
        self._commit_event(event)
        return TransitionResult(
            event_id=event.event_id,
            applied=True,
            state_version=self._version,
            message=f"Incident {event.incident_id} created in Digital Twin",
        )

    def _handle_incident_status_changed(self, event: IncidentStatusChangedEvent) -> TransitionResult:
        incident = self._incidents.get(event.incident_id)
        if incident is None:
            raise StateTransitionError(f"Incident {event.incident_id} does not exist")

        updated, is_no_op = apply_incident_status_transition(incident, event)
        if is_no_op:
            self._seen_event_ids[event.event_id] = self._version
            return TransitionResult(event_id=event.event_id, applied=False, state_version=self._version, is_no_op=True)

        self._incidents[event.incident_id] = updated
        self._commit_event(event)
        return TransitionResult(
            event_id=event.event_id,
            applied=True,
            state_version=self._version,
            message=f"Incident {event.incident_id} status updated to {event.new_status.value}",
        )

    def _handle_flood_updated(self, event: FloodUpdatedEvent) -> TransitionResult:
        fz = self._flood_zones.get(event.flood_zone_id)
        updated, is_no_op = apply_flood_transition(fz, event)
        if is_no_op:
            self._seen_event_ids[event.event_id] = self._version
            return TransitionResult(event_id=event.event_id, applied=False, state_version=self._version, is_no_op=True)

        self._flood_zones[event.flood_zone_id] = updated
        self._commit_event(event)
        return TransitionResult(
            event_id=event.event_id,
            applied=True,
            state_version=self._version,
            message=f"Flood zone {event.flood_zone_id} updated",
        )

    def _handle_vulnerability_updated(self, event: VulnerabilityUpdatedEvent) -> TransitionResult:
        vg = self._vulnerable_groups.get(event.vulnerable_group_id)
        updated, is_no_op = apply_vulnerability_transition(vg, event)
        if is_no_op:
            self._seen_event_ids[event.event_id] = self._version
            return TransitionResult(event_id=event.event_id, applied=False, state_version=self._version, is_no_op=True)

        self._vulnerable_groups[event.vulnerable_group_id] = updated
        self._commit_event(event)
        return TransitionResult(
            event_id=event.event_id,
            applied=True,
            state_version=self._version,
            message=f"Vulnerable group {event.vulnerable_group_id} updated",
        )

    def _handle_population_updated(self, event: PopulationUpdatedEvent) -> TransitionResult:
        pop = self._populations.get(event.population_id)
        updated, is_no_op = apply_population_transition(pop, event)
        if is_no_op:
            self._seen_event_ids[event.event_id] = self._version
            return TransitionResult(event_id=event.event_id, applied=False, state_version=self._version, is_no_op=True)

        self._populations[event.population_id] = updated
        self._commit_event(event)
        return TransitionResult(
            event_id=event.event_id,
            applied=True,
            state_version=self._version,
            message=f"Population region {event.population_id} updated",
        )

    def _commit_event(self, event: TwinEvent) -> None:
        """Increment version, record seen event_id, update timestamp and audit log."""
        self._version += 1
        self._updated_at = event.timestamp
        self._seen_event_ids[event.event_id] = self._version

        logged_event = event.model_copy(update={
            "metadata": {**event.metadata, "state_version": self._version}
        })
        self._event_log.append(logged_event)

    # -------------------------------------------------------------------------
    # Snapshot & Replay
    # -------------------------------------------------------------------------

    def create_snapshot(self) -> TwinSnapshot:
        """Capture deterministic point-in-time snapshot of current state."""
        return TwinSnapshot(
            state_version=self._version,
            timestamp=self._updated_at,
            roads={k: v.model_copy(deep=True) for k, v in self._roads.items()},
            bridges={k: v.model_copy(deep=True) for k, v in self._bridges.items()},
            hospitals={k: v.model_copy(deep=True) for k, v in self._hospitals.items()},
            shelters={k: v.model_copy(deep=True) for k, v in self._shelters.items()},
            rescue_teams={k: v.model_copy(deep=True) for k, v in self._rescue_teams.items()},
            incidents={k: v.model_copy(deep=True) for k, v in self._incidents.items()},
            flood_zones={k: v.model_copy(deep=True) for k, v in self._flood_zones.items()},
            populations={k: v.model_copy(deep=True) for k, v in self._populations.items()},
            vulnerable_groups={k: v.model_copy(deep=True) for k, v in self._vulnerable_groups.items()},
        )

    def restore_from_snapshot(self, snapshot: TwinSnapshot) -> None:
        """Restore all state entities and version directly from a snapshot."""
        self._version = snapshot.state_version
        self._updated_at = snapshot.timestamp
        self._roads = {k: v.model_copy(deep=True) for k, v in snapshot.roads.items()}
        self._bridges = {k: v.model_copy(deep=True) for k, v in snapshot.bridges.items()}
        self._hospitals = {k: v.model_copy(deep=True) for k, v in snapshot.hospitals.items()}
        self._shelters = {k: v.model_copy(deep=True) for k, v in snapshot.shelters.items()}
        self._rescue_teams = {k: v.model_copy(deep=True) for k, v in snapshot.rescue_teams.items()}
        self._incidents = {k: v.model_copy(deep=True) for k, v in snapshot.incidents.items()}
        self._flood_zones = {k: v.model_copy(deep=True) for k, v in snapshot.flood_zones.items()}
        self._populations = {k: v.model_copy(deep=True) for k, v in snapshot.populations.items()}
        self._vulnerable_groups = {k: v.model_copy(deep=True) for k, v in snapshot.vulnerable_groups.items()}

        if self._routing_overlay is not None:
            self._sync_all_roads_to_overlay()

    @classmethod
    def replay(
        cls,
        initial_snapshot: TwinSnapshot,
        events: List[TwinEvent],
        routing_overlay: Optional[StateOverlay] = None,
    ) -> "DigitalTwinStateManager":
        """
        Deterministic event replay:
        Restores state from an initial snapshot and applies a sequential list of events.
        Produces mathematically identical final state to live execution.
        """
        manager = cls(routing_overlay=routing_overlay, initial_version=initial_snapshot.state_version)
        manager.restore_from_snapshot(initial_snapshot)

        for evt in events:
            manager.apply_event(evt)

        return manager

    def fork(self, routing_overlay: Optional[StateOverlay] = None) -> "DigitalTwinStateManager":
        """
        Create an independent, isolated clone of this DigitalTwinStateManager
        at the current state version.
        Mutations on the forked twin will NEVER affect this live state authority.
        """
        snapshot = self.create_snapshot()
        overlay = routing_overlay if routing_overlay is not None else (
            self._routing_overlay.clone() if self._routing_overlay is not None else None
        )
        forked = DigitalTwinStateManager(routing_overlay=overlay, initial_version=snapshot.state_version)
        forked.restore_from_snapshot(snapshot)
        # Copy event log & seen ids
        forked._event_log = [e.model_copy(deep=True) for e in self._event_log]
        forked._seen_event_ids = dict(self._seen_event_ids)
        return forked


    # -------------------------------------------------------------------------
    # Phase 08 StateOverlay Synchronization
    # -------------------------------------------------------------------------

    def _sync_road_to_overlay(self, road: RoadEntity) -> None:
        if self._routing_overlay is None:
            return
        source = OverrideSource.SIMULATION if road.source == "SIMULATION" else (
            OverrideSource.TEST_FIXTURE if road.source == "TEST_FIXTURE" else OverrideSource.FIELD_REPORT
        )
        self._routing_overlay.set_road_override(
            road_id=road.road_id,
            status=road.status,
            source=source,
            speed_limit_kmh=road.speed_kmh,
            reason=road.reason or "Digital Twin synchronization",
        )

    def _sync_bridge_to_overlay(self, bridge: BridgeEntity) -> None:
        if self._routing_overlay is None:
            return
        source = OverrideSource.SIMULATION if bridge.source == "SIMULATION" else (
            OverrideSource.TEST_FIXTURE if bridge.source == "TEST_FIXTURE" else OverrideSource.FIELD_REPORT
        )
        target_status = (
            RoadStatus.BLOCKED
            if bridge.status in (BridgeStatus.BLOCKED, BridgeStatus.COLLAPSED, BridgeStatus.CLOSED)
            else (RoadStatus.RESTRICTED if bridge.status in (BridgeStatus.RESTRICTED, BridgeStatus.SUBMERGED) else RoadStatus.OPEN)
        )
        self._routing_overlay.set_bridge_override(
            bridge_id=bridge.bridge_id,
            status=target_status,
            source=source,
            reason=bridge.reason or "Digital Twin synchronization",
        )

    def _sync_all_roads_to_overlay(self) -> None:
        if self._routing_overlay is None:
            return
        for road in self._roads.values():
            self._sync_road_to_overlay(road)
        for bridge in self._bridges.values():
            self._sync_bridge_to_overlay(bridge)
