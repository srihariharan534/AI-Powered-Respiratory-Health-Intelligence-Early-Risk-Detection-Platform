# NEXUS What-If Scenario Engine

## 1. Purpose & Core Objective
The **NEXUS What-If Scenario Engine** is an isolated scenario simulation and counterfactual impact-analysis layer that enables emergency coordinators to test hypothetical conditions:
* *"What happens if flood levels rise by +1.0 meter?"*
* *"What happens if bridge B-001 fails?"*
* *"What happens if hospital H-001 reaches 100% capacity?"*
* *"What happens if available rescue units are reduced?"*
* *"What happens if multiple disaster conditions occur simultaneously?"*

It answers counterfactual questions across infrastructure and routing **before** conditions materialize.

---

## 2. Critical Safety Rule: Zero Live State Mutation
> **MANDATORY SAFETY BOUNDARY:**  
> The What-If Scenario Engine **never** mutates the live Digital Twin operational state during preview executions.

Every scenario execution strictly adheres to the isolated lifecycle:
```text
LIVE DIGITAL TWIN (vX)
         │
         │ .fork() (Copy-on-Write State Snapshot)
         ▼
ISOLATED SCENARIO STATE
         │
         ├─ Apply hypothetical modifications (Bridge, Flood, Hospital, Resources)
         ├─ Execute Phase 10 Flood Simulation
         ├─ Evaluate Phase 08 Dynamic Rerouting
         ▼
IMPACT ANALYSIS & CAUSAL DELTAS
         │
         ▼
WHAT-IF SCENARIO RESULT (Returned to caller)
         │
         ▼
DISCARD ISOLATED STATE (Live Digital Twin remains vX, 100% untouched)
```

---

## 3. Architecture & Subsystem Reuse
The What-If engine acts as a pure orchestration layer that reuses verified subsystem foundations:
- **Phase 09 (Digital Twin)**: Forked isolated state managers (`DigitalTwinStateManager.fork()`) enforce event-driven state transitions (`TwinEvent`, `BridgeStatusChangedEvent`, `CapacityUpdatedEvent`, `RoadStatusChangedEvent`).
- **Phase 10 (Flood Simulation)**: Executes `FloodSimulationEngine` with `ElevationGrid` or explicit flood polygon extents and evaluates road exposure thresholds.
- **Phase 08 (Dynamic Rerouting)**: Reuses `DynamicRerouter` and `StateOverlay.clone()` to evaluate route invalidation and compute dynamic bypass routes.

```text
               ┌────────────────────────┐
               │    WhatIfScenario      │
               │   (Base Version X)     │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │  WhatIfScenarioEngine  │
               └─────┬────────────┬─────┘
                     │            │
       ┌─────────────┘            └─────────────┐
       ▼                                        ▼
Phase 10 Flood Simulation              Phase 08 Dynamic Rerouting
(Extent & Submergence)                 (Bypass Recalculation)
       │                                        │
       └─────────────┬──────────────────────────┘
                     ▼
       ┌────────────────────────┐
       │  WhatIfScenarioResult  │
       │  (Deltas, Explanations,│
       │   Causal Chain Steps)  │
       └────────────────────────┘
```

---

## 4. Scenario Types & Modifications
Implemented in [`services/simulation/models.py`](file:///c:/Users/pabit/Downloads/NEXUS/services/simulation/models.py):
1. **`FloodLevelModification`**:
   - Depth increments ($+X\text{ m}$), absolute levels, or explicit hazard polygons.
   - Configurable road closure rules (`auto_close_roads = True`, `road_closure_threshold_meters`).
2. **`BridgeFailureModification`**:
   - Marks target bridge as `BLOCKED`.
   - Causally propagates closure to the associated road (`propagate_to_road = True`).
3. **`HospitalCapacityModification`**:
   - Simulates saturation or reduction in available bed/ICU capacity.
   - Strictly enforces domain boundary ($0 \le \text{available} \le \text{capacity}$).
4. **`ResourceShortageModification`**:
   - Reduces available rescue teams/vehicles (`available_quantity`).
5. **`Compound Scenario`**:
   - Sequentially applies multiple simultaneous modifications (e.g. Flood Surge + Bridge Collapse + Hospital Saturation).

---

## 5. State Version Validation & Conflict Prevention
- Every `WhatIfScenario` specifies `base_state_version`.
- If the live Digital Twin is at version $V_1$ but the scenario requests execution against $V_0$, the engine raises `StateVersionConflictError`.
- Prevents silent stale calculations.

---

## 6. Traceable Counterfactual Explanations
Explanations are synthesized deterministically from actual state transitions (zero LLM hallucination):
- **Impact Deltas**: Area flooded ($\text{m}^2$), newly blocked roads, route length delta ($\text{m}$), duration delta ($\text{s}$), facility capacity deltas.
- **Causal Chain**:
  ```text
  Step 1: Hypothetical failure of Bridge B-102
  Step 2: Bridge B-102 failure cascade -> Road ROAD-102 transitioned to BLOCKED
  Step 3: Active route intercepted by blocked infrastructure
  Step 4: Route invalidated; dynamically rerouted (delta: +300.0m)
  ```

---

## 7. Scope Boundaries
- **No Machine Learning / LLMs**: Fully deterministic, explainable scenario simulation.
- **No Recommendation Engine**: Reports consequences and impact deltas; does not decide dispatch or triage priorities (Phase 12+).
- **No Frontend**: Command Center UI visualization belongs to dedicated presentation phases.
