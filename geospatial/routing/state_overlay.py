"""
Operational State Overlay Manager.
Maintains a versioned, non-destructive layer of operational road overrides on top
of the immutable base road network.
"""

import uuid
from typing import Any, Dict, List, Optional, Set

from geospatial.routing.dynamic_state import (
    OverrideSource,
    RoadStateChangedEvent,
    RoadStateOverride,
)
from services.api.app.schemas.road import Accessibility, RoadStatus


class StateOverlay:
    """
    In-memory operational overlay tracking dynamic road state overrides.
    Base OSM road graph remains completely immutable.
    """

    def __init__(self) -> None:
        self._overrides: Dict[str, RoadStateOverride] = {}  # road_id -> RoadStateOverride
        self._bridge_to_road: Dict[str, str] = {}  # bridge_id -> road_id
        self._road_to_edges: Dict[str, Set[str]] = {}  # road_id -> Set[edge_id]
        self._version: int = 1
        self._events: List[RoadStateChangedEvent] = []

    @property
    def version(self) -> int:
        """Current operational state version number."""
        return self._version

    def register_road_edge(self, road_id: str, edge_id: str, bridge_id: Optional[str] = None) -> None:
        """Index association between road_id, edge_id, and optional bridge_id."""
        if road_id not in self._road_to_edges:
            self._road_to_edges[road_id] = set()
        self._road_to_edges[road_id].add(edge_id)

        if bridge_id:
            self._bridge_to_road[bridge_id] = road_id

    def set_road_override(
        self,
        road_id: str,
        status: RoadStatus,
        accessibility: Optional[Accessibility] = None,
        speed_limit_kmh: Optional[float] = None,
        reason: str = "Operational update",
        source: OverrideSource = OverrideSource.SIMULATION,
        bridge_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RoadStateOverride:
        """
        Apply or update a dynamic state override for a road.
        Increments state version and records an internal event.
        """
        if not road_id:
            raise ValueError("road_id cannot be empty")

        prev_override = self._overrides.get(road_id)
        prev_status = prev_override.status if prev_override else None

        override = RoadStateOverride(
            road_id=road_id,
            status=status,
            accessibility=accessibility,
            speed_limit_kmh=speed_limit_kmh,
            reason=reason,
            source=source,
            bridge_id=bridge_id,
            metadata=metadata or {},
        )
        self._overrides[road_id] = override
        self._version += 1

        event = RoadStateChangedEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            road_id=road_id,
            previous_status=prev_status,
            new_status=status,
            reason=reason,
            source=source,
            state_version=self._version,
        )
        self._events.append(event)
        return override

    def set_bridge_override(
        self,
        bridge_id: str,
        status: RoadStatus,
        reason: str = "Bridge status update",
        source: OverrideSource = OverrideSource.SIMULATION,
    ) -> Optional[RoadStateOverride]:
        """
        Propagate a bridge operational event to its associated road and edges.
        """
        road_id = self._bridge_to_road.get(bridge_id)
        if not road_id:
            # Fallback convention: if road_id not indexed, try matching standard OSM-ROAD prefix
            road_id = bridge_id.replace("BRIDGE-", "OSM-ROAD-")

        return self.set_road_override(
            road_id=road_id,
            status=status,
            reason=reason,
            source=source,
            bridge_id=bridge_id,
        )

    def clear_road_override(
        self,
        road_id: str,
        reason: str = "Restored to base OSM state",
        source: OverrideSource = OverrideSource.SIMULATION,
    ) -> bool:
        """
        Remove dynamic override for a road, returning it to baseline OSM state.
        Increments state version and records event.
        """
        if road_id in self._overrides:
            prev_status = self._overrides[road_id].status
            del self._overrides[road_id]
            self._version += 1

            event = RoadStateChangedEvent(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                road_id=road_id,
                previous_status=prev_status,
                new_status=None,
                reason=reason,
                source=source,
                state_version=self._version,
            )
            self._events.append(event)
            return True
        return False

    def clear_all_overrides(self) -> int:
        """Clear all active overrides (complete rollback to baseline)."""
        count = len(self._overrides)
        if count > 0:
            self._overrides.clear()
            self._version += 1
            event = RoadStateChangedEvent(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                road_id="ALL",
                previous_status=None,
                new_status=None,
                reason="Complete rollback to baseline",
                source=OverrideSource.SIMULATION,
                state_version=self._version,
            )
            self._events.append(event)
        return count

    def get_road_override(self, road_id: str) -> Optional[RoadStateOverride]:
        """Get active override for a road, if any."""
        return self._overrides.get(road_id)

    def get_all_overrides(self) -> Dict[str, RoadStateOverride]:
        """Get dictionary of all active road overrides."""
        return dict(self._overrides)

    def get_affected_edges(self, road_id: str) -> Set[str]:
        """Get set of edge IDs associated with road_id."""
        return set(self._road_to_edges.get(road_id, set()))

    def get_effective_edge_data(self, base_edge_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge baseline edge metadata with any active dynamic state override.
        Precedence:
          Dynamic Operational State > Base OSM State.
        Does not mutate base_edge_data.
        """
        road_id = str(base_edge_data.get("road_id", ""))
        override = self._overrides.get(road_id)

        if not override:
            return base_edge_data

        # Create a shallow copy with overridden properties
        effective = dict(base_edge_data)
        effective["status"] = override.status.value
        if override.accessibility is not None:
            effective["accessibility"] = override.accessibility.value
        if override.speed_limit_kmh is not None:
            effective["speed_limit_kmh"] = override.speed_limit_kmh

        effective["override_applied"] = True
        effective["override_reason"] = override.reason
        effective["override_source"] = override.source.value
        return effective

    def clone(self) -> "StateOverlay":
        """
        Create an independent deep copy of this operational overlay.
        Mutations on the clone do not affect the original.
        """
        cloned = StateOverlay()
        cloned._overrides = {k: v.model_copy(deep=True) for k, v in self._overrides.items()}
        cloned._bridge_to_road = dict(self._bridge_to_road)
        cloned._road_to_edges = {k: set(v) for k, v in self._road_to_edges.items()}
        cloned._version = self._version
        cloned._events = [e.model_copy(deep=True) for e in self._events]
        return cloned

