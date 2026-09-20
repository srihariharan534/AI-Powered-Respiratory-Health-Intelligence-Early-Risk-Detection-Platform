# Facility Operational Management — Architecture & Operational Design

NEXUS Phase 16 establishes authoritative, versioned operational management for **Hospitals** and **Shelters**.

---

## 1. Domain Model and Canonical Contracts

NEXUS facilities strictly adhere to the canonical Phase 04 contracts:
- `data/schemas/hospital.schema.json`
- `data/schemas/shelter.schema.json`

### Hospitals
- **Key Attributes**: `hospital_id`, `name`, `location` (GeoJSON Point in EPSG:4326), `status`, `accessibility`, `capacity`, `available_capacity`, `emergency_available`, `icu_available`, `source`, `last_updated`.
- **Controlled Statuses**:
  - `OPERATIONAL`: Triage and admissions active.
  - `OVERLOADED`: High intake approaching or exceeding manageable surge.
  - `EVACUATING`: Active patient transfer or facility evacuation.
  - `CLOSED`: Inaccessible or structurally compromised.
- **Emergency Availability**: Explicit boolean representation of emergency trauma ward capability.
- **ICU Availability**: Discrete count of remaining operational intensive care beds.

### Shelters
- **Key Attributes**: `shelter_id`, `name`, `location` (GeoJSON Point in EPSG:4326), `status`, `accessibility`, `capacity`, `available_capacity`, `has_power_backup`, `has_potable_water`, `source`, `last_updated`.
- **Controlled Statuses**:
  - `OPEN`: Accepting evacuees.
  - `AT_CAPACITY`: Safely full; no intake.
  - `STANDBY`: Staged and prepared for disaster activation.
  - `CLOSED`: Decommissioned or inaccessible.

---

## 2. Capacity Semantics & Validation Rules

### Mathematical Invariant
$$\forall \text{ facility}: 0 \le \text{available\_capacity} \le \text{capacity}$$

- Total capacity represents maximum licensed/physical capacity.
- Available capacity represents currently unoccupied, operational capacity.
- Rejection criteria:
  - Negative total capacity
  - Negative available capacity
  - $\text{available\_capacity} > \text{capacity}$
- Clamping is strictly forbidden; structured validation errors are raised.

---

## 3. Digital Twin Integration & State Versioning

Hospitals and shelters are first-class operational entities inside the central `DigitalTwinStateManager`:
- Operational entities: `HospitalEntity`, `ShelterEntity`.
- Domain events:
  - `CapacityUpdatedEvent`: Modifies `capacity`, `available_capacity`, and optional `icu_available`.
  - `FacilityStatusChangedEvent`: Transitions operational status with audit reason and actor.
- State Versioning & Optimistic Concurrency:
  - Every valid event commits a state transition and increments `state_version` ($v \to v + 1$).
  - REST endpoints accept `expected_state_version`. If another operator updated the facility in the interim, a structured HTTP `409 Conflict` (`STATE_VERSION_CONFLICT`) is returned. Overwrites are prevented.
- Append-Only Audit Trail:
  - Immutable timeline capturing `who`, `what`, `when`, `previous_state`, `new_state`, and `details`.

---

## 4. Flood Exposure Spatial Analysis

### The Critical Rule
$$\text{EXPOSED} \ne \text{CLOSED} \quad \text{and} \quad \text{EXPOSED} \ne \text{DAMAGED}$$

- When a facility's WGS84 point coordinates intersect a simulated flood extent polygon (from Phase 10 Inundation Engine or What-If Scenarios), it is marked:
  - `Flood Exposure: EXPOSED`
  - `Scenario: <SCENARIO_ID>`
  - `Mode: SIMULATION`
- The spatial engine confirms geometric containment/intersection, but does **NOT** trigger automatic closure. Many facilities operate multi-story medical wards or deploy localized flood berms. Closure requires human operational assessment and confirmed status transition.
- If no flood scenario is active:
  - `Flood Exposure: Not evaluated`

---

## 5. What-If Counterfactual Scenario Integration

Phase 16 integrates with Phase 11 What-If Scenario Engine:
- `HospitalCapacityModification`: Evaluates counterfactual saturation (e.g. `available_capacity = 0`).
- `ShelterCapacityModification`: Evaluates relief camp exhaustion (e.g. `available_capacity = 0`).
- **Zero-Mutation Guarantee**: What-If scenarios execute exclusively against forked, isolated state copies. Authoritative live hospital and shelter records remain untouched.

---

## 6. GIS Map & Command Center Integration

- **Table $\leftrightarrow$ Map Synchronization**:
  - Selecting a facility row in `/hospitals` or `/shelters` centers the Leaflet GIS map, highlights the marker, and opens the detail inspector.
  - Clicking any facility marker on the map selects the facility and displays its operational attributes.
- **Visual Symbology**:
  - Distinguishes operational status using color and textual badge semantics.
  - Highlights flood-exposed facilities with blue boundary halo and warning tooltip.
  - Labels data provenance clearly (`REAL`, `SIMULATION`, or `DEMO`).

---

## 7. Hard Scope Boundaries (Anti-Features)

To adhere strictly to platform boundaries:
- **NO AI Facility Ranking**: Does not recommend "best hospital" or "optimal shelter".
- **NO Patient Allocation**: Bed assignments and triage routing belong to future recommendation logic.
- **NO Route Optimization**: Dynamic routing is delegated to Phase 07/08 routing engines.
- **NO Vulnerability Prioritization**: Demographic scoring is reserved for Phase 27.
