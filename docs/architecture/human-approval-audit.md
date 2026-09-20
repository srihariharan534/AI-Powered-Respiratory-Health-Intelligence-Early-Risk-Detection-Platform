# Human Approval & Audit Architecture (Phase 21)

## 1. Overview & Core Philosophy

The NEXUS platform operates under a strict, non-negotiable constitutional safety principle:

> **NEXUS recommends. An authorized human decides. The system records what happened.**

The platform analyzes telemetry, evaluates spatial risk models, identifies nearest resilient facilities, and calculates safe routes. However, NEXUS **never executes autonomous operational actions**. It will never:
- Automatically dispatch search and rescue squads;
- Automatically order community evacuations;
- Automatically modify road access statuses or shut bridges;
- Automatically divert ambulances without physician/dispatcher sign-off;
- Automatically close hospitals or shelters.

Every operational recommendation must have `requires_human_approval: true`, anchored to an immutable Digital Twin state version.

```text
RECOMMENDATION GENERATED
           ↓
        PENDING
           ↓
   HUMAN REVIEWS EVIDENCE
           ↓
 ┌────────────────────────┐
 │                        │
APPROVE                 REJECT
 │                        │
 ↓                        ↓
APPROVED                REJECTED
 └───────────┬────────────┘
             │
     APPEND-ONLY AUDIT
```

---

## 2. Recommendation Lifecycle & State Machine

Status transitions are governed by the centralized `RecommendationStateMachine` (`services/recommendations/governance/state_machine.py`):

```text
PENDING   ──►  APPROVED  (Terminal)
          ──►  REJECTED  (Terminal)
          ──►  EXPIRED   (Terminal)
```

All other transitions (e.g., `APPROVED -> PENDING`, `APPROVED -> REJECTED`, `REJECTED -> APPROVED`, or `EXPIRED -> APPROVED`) are strictly rejected with `InvalidStateTransitionError` (`HTTP 400 Bad Request`).

---

## 3. Server-Enforced Role-Based Access Control (RBAC)

Authorization is verified server-side on every request using headers (`X-Actor-Id`, `X-Actor-Role`). Client-side UI button visibility is never treated as a security perimeter.

| Role | View Recs | Generate Recs | Approve Recs | Reject Recs | Expire Recs | View Audit |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **VIEWER** | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ |
| **FIELD_OFFICER** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **OPERATOR** | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ |
| **APPROVER** | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ |
| **COMMANDER** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **ADMIN** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Attempts by unauthorized roles to approve or reject recommendations return `HTTP 403 Forbidden` and append an `APPROVAL_BLOCKED` audit record.

---

## 4. State Freshness & Precondition Validation

Before any approval transaction is committed, the backend verifies:
1. **State Version Invariance**:
   $$\text{rec.source\_state\_version} == \text{current\_digital\_twin.state\_version}$$
   If the Digital Twin has advanced (e.g. `state-v100` vs `state-v101`), the recommendation is marked `EXPIRED` and the approval is rejected with `HTTP 409 Conflict` (`RECOMMENDATION_STALE`).
2. **Operational Entity Preconditions**:
   - **Incidents**: If the incident target has transitioned to `RESOLVED` or `CANCELLED`, approval is blocked.
   - **Hospitals**: If the receiving hospital has status `CLOSED` or `EVACUATING`, or its `available_capacity <= 0`, approval is blocked.
   - **Shelters**: If the target relief shelter has status `CLOSED` or `AT_CAPACITY`, or its `available_capacity <= 0`, approval is blocked.
3. **Simulation Isolation**:
   Recommendations generated with mode `SIMULATION` or `DEMO` cannot be approved into live operational state.

---

## 5. Append-Only Audit Ledger

The `AuditLedger` (`services/recommendations/governance/audit_ledger.py`) provides an immutable, thread-safe record of all governance lifecycle events:

- `RECOMMENDATION_CREATED`: Generated recommendation with target snapshot.
- `RECOMMENDATION_VIEWED`: Recorded when a coordinator inspects a recommendation.
- `RECOMMENDATION_APPROVED`: Authorized with operator identity, role, timestamp, and rationale.
- `RECOMMENDATION_REJECTED`: Recorded with mandatory operator justification.
- `RECOMMENDATION_EXPIRED`: Invalidation due to state advancement or administrative action.
- `APPROVAL_BLOCKED`: Security or state-conflict audit event.

Direct mutation or deletion of audit events (`PUT /audit`, `DELETE /audit`) is strictly prohibited.

---

## 6. Concurrency & Idempotency

- **Concurrency Safety**: In-memory and service operations utilize re-entrant thread locking (`threading.Lock`) to prevent race conditions where two operators might concurrently approve and reject the same proposal. Only the first valid transition succeeds.
- **Idempotency**: Repeated approval requests submitted with the same `idempotency_key` return the cached `RecommendationDecisionRecord` without generating redundant audit log entries.
