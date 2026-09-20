# NEXUS Command Center Architecture

## Overview

The **NEXUS Command Center** is the primary operational interface for District Emergency Operations Center (EOC) coordinators, disaster response commanders, and agency decision-makers.

Built in **Phase 12 (Command Center Foundation)**, the application delivers a mission-critical web shell focused on operational safety, honest state reporting, and resilient offline-first design.

---

## 1. Safety & Operational Principles

- **Information Hierarchy**: Prioritizes `RISK` → `DECISION` → `ACTION` → `CHANGE`.
- **Honest Telemetry & Unambiguous Modes**: Data mode is always visible (`REAL DATA`, `SIMULATION`, `DEMO MODE`). No simulated or synthetic data is ever masqueraded as live emergency telemetry.
- **Digital Twin as Operational Authority**: All operational state reflects the versioned authority (`State Version: X`). If state is unavailable or offline, the interface explicitly communicates `Awaiting API connection` or `DATA UNAVAILABLE` with actionable retry mechanisms.
- **Restrained Visual Language**: Avoids neon cyberpunk aesthetics, rainbow charts, and distracting decorative animations. Uses a high-contrast dark theme with consistent severity semantics.

---

## 2. Component & Layout Architecture

```text
┌──────────────────────────────────────────────────────────┐
│ NEXUS HEADER                                             │
│ Brand | Status (ONLINE) | Mode (REAL) | State Version | Role
├───────────────┬──────────────────────────────────────────┤
│ SIDEBAR       │ MAIN CONTENT AREA                        │
│               │                                          │
│ COMMAND       │ [ Routed Page Outlet ]                   │
│   Dashboard   │  - Operational Overview                  │
│ OPERATIONS    │  - Incident Management                   │
│   Incidents   │  - Facility Coordination                 │
│ FACILITIES    │  - Scenario Sandboxing                   │
│   Hospitals   │  - Authority State Ledger                │
│   Shelters    │  - Governance & Judge Mode               │
│   Vulnerab.   │                                          │
│ SIMULATION    │                                          │
│   What-If     │                                          │
│   DigitalTwin │                                          │
│ DECISION      │                                          │
│   Recomm.     │                                          │
│ GOVERNANCE    │                                          │
│   Audit       │                                          │
│ DEMO          │                                          │
│   Judge Mode  │                                          │
├───────────────┴──────────────────────────────────────────┤
│ FOOTER: Authority Source | Mode | Last Synchronized Time │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Global Application State

Managed via React Context (`src/context/AppContext.tsx`):

- `connectionStatus`: `'ONLINE' | 'DEGRADED' | 'OFFLINE'` (listens to browser network events and backend health probes).
- `dataMode`: `'REAL' | 'SIMULATION' | 'DEMO' | 'UNKNOWN'`.
- `stateVersionInfo`: Authoritative version number (`version: number | null`), timestamp, and authority identifier.
- `currentUser`: Operational coordinator role (`COMMANDER`, `FIELD_OFFICER`, etc.) and jurisdiction.
- `lastSyncTime`: Accurate local timestamp of the last successful digital-twin sync.

---

## 4. API Client & Resilient Error Handling

Centralized in `src/services/api-client.ts`:

- Configurable base URL (via `VITE_API_BASE_URL` or fallback to `http://localhost:8000`).
- Configurable request timeout (defaults to 8000ms) with `AbortController` cancellation.
- Unified error modeling into `ApiError`:
  - `NETWORK_ERROR` (code 0)
  - `TIMEOUT` (status 408)
  - `HTTP_4xx` / `HTTP_5xx` (structured error response parsing)
  - `PARSE_ERROR` (malformed JSON response)
- User-facing error presentation masks technical call stacks and presents plain, actionable language.

---

## 5. Scope Boundaries

- **Phase 12 Scope**: Foundation, routing, global state, UI primitives, status indicators, API client, tests.
- **Phase 13 Scope**: Live GIS Dashboard (Leaflet / MapLibre, animated flood extents, spatial road graphs, route overlays).
- **Phase 14 Scope**: Dedicated Judge Mode evaluation walkthrough.
- **Phase 15+ Scope**: Full facility, vulnerability, and recommendation scoring engines.
