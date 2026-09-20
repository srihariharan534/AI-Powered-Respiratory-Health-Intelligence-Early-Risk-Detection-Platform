# NEXUS Security & Role-Based Access Control (RBAC)

## 1. Overview

In disaster coordination, operations require role-segregated authorization to ensure that high-impact actions (such as authorizing civilian rescue priorities or shelter openings) are only performed by verified incident commanders and approvers.

---

## 2. Roles & Permissions

| Role | Scope | Permitted Endpoints |
|---|---|---|
| `VIEWER` | Read-only access to GIS maps, incidents, and proposed recommendations. | `GET /api/v1/recommendations`, `GET /api/v1/audit/ledger` |
| `FIELD_OFFICER` | Tactical updates from the field; view local recommendations. | `GET /api/v1/recommendations` |
| `OPERATOR` | Triage desk coordinators; view and generate recommendations. | `POST /api/v1/recommendations/generate`, `GET /api/v1/recommendations` |
| `APPROVER` | Authorized senior personnel responsible for operational approvals. | `POST /api/v1/recommendations/{id}/approve`, `POST /api/v1/recommendations/{id}/reject` |
| `COMMANDER` | Full incident jurisdiction; can generate, approve, reject, and expire. | Full operational recommendations authority |
| `ADMIN` | System and data management; emergency administrative overrides. | Full operational and governance authority |

---

## 3. Server-Side Enforcement

All governance endpoints inspect:
- `X-Actor-Id`: Unique coordinator username or tactical callsign.
- `X-Actor-Role`: Explicit governance role (`COMMANDER`, `APPROVER`, `OPERATOR`, `VIEWER`).

Requests lacking required permissions return `HTTP 403 Forbidden` and log an `APPROVAL_BLOCKED` security event to the audit ledger.
