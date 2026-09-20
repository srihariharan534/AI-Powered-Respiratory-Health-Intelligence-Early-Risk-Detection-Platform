# NEXUS Digital Twin — Emergency Operational State Authority

## 1. Digital Twin Definition
For NEXUS:
> **The Digital Twin is a versioned operational representation of entities, relationships, and state transitions in the emergency environment.**

It is NOT a visual 3D simulation or rendering engine. It is the **shared operational state authority** that answers:
- What is the current operational status of each asset?
- What changed?
- When did it change? (Timezone-aware UTC)
- Why did it change?
- What authoritative source caused the change?
- Which state version represents this reality?

> **Important**: The NEXUS Digital Twin is an operational state model, not a claim of perfect real-world representation. It models operational uncertainty and incomplete information.

---

## 2. Architecture & The Single Source of Truth
The Digital Twin prevents fragmented state across subsystems:

```text
               ┌────────────────────────┐
               │   Observation / Field  │
               └───────────┬────────────┘
                           │ Domain Event
                           ▼
               ┌────────────────────────┐
               │      Digital Twin      │
               │  (State Authority)     │
               └───────────┬────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
Operational Overlay   Future Sim           Future AI
(Phase 08 Routing)
```

No subsystem (Command Center, Field PWA, Emergency Routing, Resource Planning) maintains an independent copy of operational truth.

---

## 3. Entity Model
Typed operational representations located in `digital_twin/entities/`:
- **`RoadEntity`**: Tracks `road_id`, operational `status` (`OPEN`, `RESTRICTED`, `BLOCKED`, `UNKNOWN`), `accessibility`, `speed_kmh`, `associated_bridge_ids`, timestamp, and provenance source. (Graph geometry is owned by Phase 05/Phase 06).
- **`BridgeEntity`**: Tracks `bridge_id`, `road_id`, `status` (`OPEN`, `RESTRICTED`, `BLOCKED`, `COLLAPSED`, `SUBMERGED`, `CLOSED`), vertical clearance, and causes cascading road status updates.
- **`HospitalEntity`**: Tracks `hospital_id`, bed `capacity`, `available_capacity` ($0 \le \text{available} \le \text{capacity}$), ICU availability, and accessibility.
- **`ShelterEntity`**: Tracks `shelter_id`, maximum capacity, available occupancy ($0 \le \text{available} \le \text{capacity}$), and operational status.
- **`RescueTeamEntity`**: Tracks `rescue_team_id`, unit `status` (`AVAILABLE`, `DISPATCHED`, `ON_SCENE`, `RETURNING`, `OFF_DUTY`, `MAINTENANCE`), location, vehicle type, and capacity.
- **`IncidentEntity`**: Conforms to the Phase 04 incident schema contract (`incident_id`, `event_type`, `severity`, `status`, `location`, `reported_by`, `priority`).
- **`FloodZoneEntity`**: Spatial observed flood extents and water depth in meters. Distinguishes unknown depth (`None`) from dry ground (`0.0`).
- **`PopulationEntity`**: Tracks regional estimated headcounts (`population_id`, `count`, `location`).
- **`VulnerableGroupEntity`**: References demographic vulnerability groupings (`vulnerable_group_id`, `category`, `count`, `location`). Does NOT calculate prioritization scores.

---

## 4. Event Model & Immutability
Events are defined in `digital_twin/events/` and inherit from `TwinEvent`:
- Immutable once created (`frozen = True`).
- Carry stable `event_id`, `event_type`, `timestamp` (UTC), `source` (`EventSource`), `reason`, and causal link (`caused_by_event_id`).
- Supported events:
  - `RoadStatusChangedEvent`
  - `BridgeStatusChangedEvent`
  - `IncidentCreatedEvent`
  - `IncidentStatusChangedEvent`
  - `CapacityUpdatedEvent`
  - `FloodUpdatedEvent`
  - `VulnerabilityUpdatedEvent`
  - `PopulationUpdatedEvent`

---

## 5. State Transitions & Validation
State transitions in `digital_twin/state/transitions.py` are pure, deterministic functions:
1. Validate event schema against business constraints (e.g. `available_capacity <= capacity`).
2. Compare new values with current entity state.
3. Return `(updated_entity, is_no_op)`.
4. Rejected transitions or invalid schemas raise explicit `ValueError` / `StateTransitionError`.

---

## 6. Versioning, Idempotency & No-Ops
- **Versioning**: Every event that produces an actual operational state change increments `state_version` monotonically ($V \to V + 1$).
- **Idempotency**: Every processed event is indexed by `event_id`. Re-submitting an already processed `event_id` returns a duplicate transition result without mutating state or incrementing the version.
- **No-Ops**: An event asserting a state identical to current state is recorded as a `no_op` without incrementing the state version.

---

## 7. Event Replay & Snapshots
- **Snapshots**: Point-in-time state captures via `TwinSnapshot(state_version, timestamp, entities...)`.
- **Replay**: `DigitalTwinStateManager.replay(initial_snapshot, events) -> DigitalTwinStateManager` replays sequential events over a baseline snapshot. Replay yields mathematically identical entity states and version counters to live execution.

---

## 8. Bridge $\to$ Road Causal Propagation
When a bridge changes operational status (e.g. `BridgeStatus.BLOCKED`), the Digital Twin propagates the closure to the associated road segment:
```text
BridgeStatusChangedEvent (B-102: BLOCKED)
        │
        ▼
RoadStatusChangedEvent (ROAD-102: BLOCKED, caused_by_event_id="EVT-B102-FAIL")
        │
        ▼
Audit Log preserves causal provenance chain
```

---

## 9. Phase 08 Dynamic Routing Integration
The Digital Twin connects directly to the Phase 08 `StateOverlay`:
```text
Digital Twin Event
        │
        ▼
DigitalTwinStateManager.apply_event()
        │
        ▼ (synchronous update)
StateOverlay.set_road_override() / set_bridge_override()
        │
        ▼
EmergencyRouter / DynamicRerouter
```
When a road is closed in the Digital Twin, any in-flight route traversing that segment is invalidated. `DynamicRerouter.evaluate_and_reroute()` immediately diverts around the incident.

---

## 10. Limitations & Out-of-Scope Boundaries
- **No Frontend**: Visual rendering belongs to later phases.
- **No AI / Recommendation Engine**: The Digital Twin records state; it does not decide dispatch or triage priorities.
- **No Hydrodynamic Simulation**: Flood extents reflect observed or imported data, not predicted future rainfall runoff.
- **In-Memory Operational Authority**: Optimized for lightweight, zero-dependency offline resilience. Persistent store sync is scheduled for Phase 25.
