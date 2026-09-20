# NEXUS Dynamic Rerouting Engine Architecture

## 1. Purpose & Phase Boundary
Phase 08 establishes the **Dynamic Rerouting Engine** on top of the immutable Phase 05 OSM road graph and Phase 07 Emergency Router.

### Explicit Boundary:
- **Phase 08 Scope**: Dynamic road/bridge operational state representation, non-destructive state overlays, affected-edge identification, route invalidation, conditional reroute triggers, route comparison metrics, and machine-readable explanations.
- **Strict Boundary**: Does **NOT** implement hydrodynamic flood simulation, ML risk scoring, recommendation rankings, human approval queues, field PWA, offline sync, or the full Digital Twin state manager (reserved for Phase 09).

---

## 2. Architecture & State Precedence

```text
       BASE ROAD GRAPH (OSM)
    (Phase 05 - Fully Immutable)
                 │
                 ▼
     ┌───────────────────────┐
     │  RoutingGraphAdapter  │
     └───────────┬───────────┘
                 │
                 ▼
     ┌───────────────────────┐
     │     StateOverlay      │ ◄── Dynamic Operational Updates (Bridge/Road Closures, Speeds)
     └───────────┬───────────┘
                 │ (Precedence: Operational Overlay > Base OSM)
                 ▼
       Effective Edge State
                 │
                 ▼
       EmergencyRouter (Phase 07 Dijkstra / A*)
                 │
                 ▼
       DynamicRerouter (Validation, Trigger, Comparison, Explanation)
```

### Precedence Rule:
1. If an operational override exists for `road_id`, its attributes (`status`, `accessibility`, `speed_limit_kmh`) take immediate precedence over baseline OSM data.
2. If no override exists, the baseline OSM road attributes are used.
3. The underlying NetworkX road graph is never mutated (edges are never removed or altered permanently).

---

## 3. Key Components & Implementation

### 3.1 State Overlay (`geospatial.routing.state_overlay.StateOverlay`)
- Maintains an in-memory dictionary of `RoadStateOverride` objects keyed by `road_id`.
- Automatically maps bridge operational events (`BRIDGE-xxx`) to associated roads (`ROAD-xxx`) and constituent graph edges.
- Supports complete or granular rollback (`clear_road_override`, `clear_all_overrides`), restoring the effective graph state to baseline.
- Tracks monotonic state versions (`version: int`) and internal `RoadStateChangedEvent` audit records.

### 3.2 Dynamic Rerouting Orchestration (`geospatial.routing.rerouting.DynamicRerouter`)
- **Route Validation (`is_route_valid`)**: Checks every traversed edge of an active route against current effective traversability rules.
- **Conditional Trigger (`evaluate_and_reroute`)**:
  - If the active route is unaffected by recent network changes, no recalculation occurs (`reroute_required = False`).
  - If any edge along the active route is compromised (e.g. status becomes `BLOCKED` or `IMPASSABLE`), the system triggers a recalculation using the Phase 07 `EmergencyRouter`.
- **Failure Mode (`NO_PATH_AFTER_STATE_CHANGE`)**: If all alternative paths are severed, the engine returns a structured result with `no_path_found = True` and `error_code = "NO_PATH_AFTER_STATE_CHANGE"` without inventing fake paths.

### 3.3 Route Comparison (`geospatial.routing.route_comparison.compare_routes`)
Computes quantitative differences between old and new routes:
- Distance delta ($\Delta$ meters)
- Duration delta ($\Delta$ seconds)
- Disjoint and overlapping edge/node sets (`removed_edges`, `added_edges`, `shared_edges`)

### 3.4 Machine-Readable Explanation (`geospatial.routing.rerouting.ReroutingExplanation`)
- Formulates a deterministic summary of the route change explaining:
  - Triggering event
  - Affected road IDs
  - Invalidation reasons
  - Metric deltas
- Completely avoids LLM generation or fabricated natural-language hallucination.

---

## 4. Verification & Testing
Validated across 8 dedicated tests in `tests/geospatial/test_dynamic_rerouting.py`:
1. Baseline route selection over multi-corridor test network.
2. State overlay precedence without base graph mutation.
3. Bridge failure propagation to associated road edges.
4. Dynamic reroute execution choosing the alternative corridor upon bridge closure.
5. Invariance when changes occur on unrelated road segments.
6. Non-destructive rollback restoring the original baseline path.
7. Structured error handling for total network partition (`NO_PATH_AFTER_STATE_CHANGE`).
8. Dynamic speed limit override increasing route duration.
