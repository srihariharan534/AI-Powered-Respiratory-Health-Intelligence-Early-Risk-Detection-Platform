# NEXUS Incident Management Architecture

## 1. Overview & Phase Scope

**Phase 15 (Incident Management)** elevates incidents from static map markers to fully managed operational entities governed by:
- **Canonical Data Contract** (Phase 04): Schema version `1.0.0`, strict WGS84 coordinate boundaries, typed severities, event categories, and structured evidence.
- **Operational Lifecycle State Machine**: Finite state machine with validated transitions.
- **Digital Twin State Authority** (Phase 09): All creations and status changes emit domain events (`IncidentCreatedEvent`, `IncidentStatusChangedEvent`), incrementing state version authority.
- **Optimistic Concurrency Control**: Guards against stale overwrites in concurrent dispatch operations using `state_version` checks.
- **Traceable Audit Log**: Immutable append-only audit entries recording `who`, `what`, `when`, and transition notes.
- **Command Center Integration** (Phases 12 & 13): Interactive dispatch roster, filter bar, detail inspector, validated action buttons, and registration form.

---

## 2. Incident Lifecycle State Machine

```text
       ┌──────────────┐
       │     OPEN     │ (Initial creation state)
       └──────┬───┬───┘
              │   │
   Acknowledge│   │Cancel
              ▼   ▼
       ┌──────────────┐
       │ ACKNOWLEDGED │
       └──────┬───┬───┘
              │   │
        Start │   │Cancel
              ▼   ▼
       ┌──────────────┐
       │ IN_PROGRESS  │
       └──────┬───┬───┘
              │   │
      Resolve │   │Cancel
              ▼   ▼
 ┌──────────┐   ┌───────────┐
 │ RESOLVED │   │ CANCELLED │  (Terminal states)
 └──────────┘   └───────────┘
```

### Transition Validation Rules:
1. `OPEN` can only transition to `ACKNOWLEDGED` or `CANCELLED`.
2. `ACKNOWLEDGED` can only transition to `IN_PROGRESS` or `CANCELLED`.
3. `IN_PROGRESS` can only transition to `RESOLVED` or `CANCELLED`.
4. `RESOLVED` and `CANCELLED` are terminal states (no further transitions permitted).
5. Attempting an illegal transition raises an `InvalidIncidentTransitionError` and returns `HTTP 422 Unprocessable Entity`.

---

## 3. Optimistic Concurrency Control

When an operational coordinator submits a status transition or detail update:
- The client sends `expected_state_version`.
- If the current server state version has advanced, the request is rejected with `HTTP 409 Conflict` (`STATE_VERSION_CONFLICT`).
- This prevents race conditions between field officers and central coordinators.

---

## 4. API Endpoints

- `POST /api/v1/incidents`: Create a new operational incident (emits `IncidentCreatedEvent`).
- `GET /api/v1/incidents`: Paginated list of incidents with query filtering (`status`, `severity`, `event_type`, `source`).
- `GET /api/v1/incidents/{incident_id}`: Full details including permitted next lifecycle actions.
- `POST /api/v1/incidents/{incident_id}/transition`: Execute validated status transition.
- `PATCH /api/v1/incidents/{incident_id}`: Update mutable fields (`severity`, `description`, `priority`).
- `GET /api/v1/incidents/{incident_id}/history`: Retrieve chronological audit log.

---

## 5. Testing & Verification

- **Domain & Lifecycle Tests**: 10 tests in `tests/unit/test_incident_management.py` validating valid/invalid transitions, idempotency, duplicate prevention, optimistic concurrency, and Digital Twin event flow.
- **Full Backend Suite**: 141 passed in `pytest tests/ -v`.
- **Frontend Unit Tests**: 20 passed in Vitest (`apps/command-center`).
- **Production Build**: Verified with Vite and TypeScript compiler.
