# NEXUS Operational Recommendation Engine (Phase 20)

## Overview

The NEXUS Operational Recommendation Engine is a deterministic, offline-capable decision-support subsystem that synthesizes validated Digital Twin state (Phase 09), incident records (Phase 15), facility operational statuses (Phase 16), routing options (Phases 07/08), and calibrated risk/uncertainty models (Phases 17/18/19).

Its mission is to formulate structured, actionable recommendations for emergency coordinators without executing autonomous operational actions.

```text
DIGITAL TWIN (State vN)
INCIDENT LOG (Phase 15)
FACILITIES (Phase 16)      ───►  OPERATIONAL RECOMMENDATION ENGINE  ───►  CANONICAL RECOMMENDATION
ROUTING (Phases 07/08)           (Hard Constraints + Scored Policy)       requires_human_approval = True
RISK / UNCERTAINTY (Phases 17-19)                                         source_state_version = "vN"
```

---

## Core Operational Tenets

1. **Mandatory Human-in-the-Loop (`requires_human_approval = True`)**:
   Every generated recommendation enforces `requires_human_approval: true` in strict accordance with the Phase 04 canonical recommendation schema (`data/schemas/recommendation.schema.json`). NEXUS never autonomously dispatches rescue teams, shuts down facilities, or modifies road statuses.

2. **State Version Invalidation (`source_state_version`)**:
   Every recommendation is bound to the immutable Digital Twin state version at the moment of generation. If the world state advances (e.g., flood waters rise or a road is blocked), earlier recommendations become stale (`EXPIRED`). Attempting to approve an expired recommendation triggers an `HTTP 409 Conflict` error to prevent acting on obsolete operational realities.

3. **Multi-Factor Deterministic Scoring**:
   Candidate entities (hospitals, shelters, priority incidents, route corridors) are evaluated through transparent normalized formulas governed by versioned policies (e.g., `policy-v1.0`). No black-box weighting or non-reproducible random selection is permitted.

4. **Honest Confidence & Uncertainty Bounds**:
   Confidence metrics reflect the multi-factor scoring outcome and are bounded by explicit uncertainty intervals derived from facility capacity volatility, travel time variance, and model risk estimates. NEXUS does not fabricate artificial confidence.

5. **Complete Audit Trail**:
   All lifecycle events (`GENERATE`, `APPROVE`, `REJECT`, `EXPIRE`) are preserved in an append-only audit ledger recording the operator identity, timestamp, decision rationale, and target state version.

---

## Domain Engines

### 1. Incident Priority Ranking Engine
- **Module**: `services/recommendations/incident_priority/priority_engine.py`
- **Objective**: Prioritize incoming emergency incidents for rescue and resource triage.
- **Criteria**:
  - Severity level (`CRITICAL` = 1.0, `HIGH` = 0.8, `MEDIUM` = 0.5, `LOW` = 0.2)
  - Modeled flood risk probability from ML models
  - Flood water depth exposure from GIS flood zones
  - Demographic vulnerability exposure
  - Evacuation route accessibility

### 2. Hospital Receiving Facility Selection Engine
- **Module**: `services/recommendations/hospital_selection/hospital_engine.py`
- **Objective**: Select the optimal medical facility for patient diversion or triage.
- **Hard Constraints**:
  - Excludes facilities marked `CLOSED` or `EVACUATING`.
  - Excludes facilities with zero available capacity (`available_capacity <= 0`).
  - Excludes facilities with impassable road accessibility.
- **Evaluation Factors**:
  - Proximity / travel distance (normalized, inverted)
  - Available bed capacity
  - Active emergency department service capability
  - Flood zone exposure

### 3. Shelter Evacuation Selection Engine
- **Module**: `services/recommendations/shelter_selection/shelter_engine.py`
- **Objective**: Direct displaced populations to safe, viable relief camps.
- **Hard Constraints**:
  - Excludes shelters marked `CLOSED` or `AT_CAPACITY`.
  - Excludes facilities with zero remaining space.
  - Excludes shelters in flooded or inaccessible zones.
- **Evaluation Factors**:
  - Proximity to incident location
  - Available intake capacity
  - Power backup resilience (generators)
  - Potable water supply availability

### 4. Evacuation Route Recommendation Engine
- **Module**: `services/recommendations/evacuation/route_recommendation.py`
- **Objective**: Provide safe transit corridors for emergency convoys and civilian evacuation.
- **Hard Constraints**:
  - Excludes flooded roads where water depth exceeds vehicle clearance thresholds.
  - Excludes impassable segments.
- **Evaluation Factors**:
  - Shortest verified safe path
  - Lowest flood hazard exposure
  - Roadway capacity and speed limits

---

## REST API Specification

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/recommendations` | List recommendations filtered by approval status or action |
| `GET` | `/api/v1/recommendations/{id}` | Retrieve single recommendation by unique identifier |
| `POST` | `/api/v1/recommendations/generate` | Generate actionable recommendations for an incident or corridor |
| `POST` | `/api/v1/recommendations/{id}/approve` | Authorize a recommendation (enforces non-stale state check) |
| `POST` | `/api/v1/recommendations/{id}/reject` | Reject a recommendation with operator rationale |
| `GET` | `/api/v1/recommendations/audit/ledger` | Query append-only audit trail |

---

## Frontend Integration

The Command Center features a dedicated **Operational Recommendations** view (`apps/command-center/src/pages/OperationalPages.tsx`):
- Filter by status (`ALL`, `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`).
- Filter by domain type (`ALL`, `INCIDENTS`, `HOSPITALS`, `SHELTERS`, `ROUTES`).
- Detailed factor breakdown pills displaying normalized decision weights.
- Bound state version display with stale-state warning alerts.
- Interactive Authorize / Reject modal flows capturing operator rationale.
