# NEXUS Synchronization Protocol (Phase 25)

## 1. Scope & Objective
This specification defines the canonical protocol for synchronizing offline operational actions created within the **NEXUS Field PWA** with the authoritative **NEXUS Backend** and **Digital Twin State Manager**.

The protocol guarantees:
* **At-least-once network delivery**: Robust against packet drops, network disconnects, and HTTP timeouts.
* **Idempotent server processing**: Re-transmitting an already processed operation produces identical responses without duplicate mutations or corrupted event logs.
* **Deterministic collision detection**: Operation ID re-use with modified payloads is detected and rejected with `IDEMPOTENCY_KEY_REUSE`.
* **Optimistic concurrency & conflict handling**: Protects life-critical state (incident severity, location, status) from silent overwrites using Digital Twin state versions.
* **No silent data loss**: Rejections, conflicts, and failures remain stored and inspectable on client and server.

---

## 2. Synchronization Data Contracts

### 2.1 Operation Schema
Each synchronized operation must adhere to the canonical envelope:

```json
{
  "operation_id": "OP-1726822800000-a1b2c3d",
  "entity_type": "INCIDENT",
  "entity_id": "INC-2026-0920-001",
  "operation_type": "CREATE",
  "payload": { ... },
  "schema_version": "1.0.0",
  "base_state_version": 12,
  "client_created_at": "2026-09-20T08:00:00.000Z",
  "client_id": "FIELD_OFFICER_01",
  "attempt_count": 0
}
```

#### Fields:
* `operation_id` (string, required): Stable UUID or timestamped identifier generated once at local capture. Must not change across retries or app restarts.
* `entity_type` (enum, required): `INCIDENT`, `EVIDENCE`, `RESOURCE_REQUEST`, `STATUS_UPDATE`.
* `entity_id` (string, required): Canonical entity identifier.
* `operation_type` (enum, required): `CREATE`, `UPDATE`, `DELETE`.
* `payload` (object, required): Domain data conforming to the respective schema (e.g. `incident.schema.json`).
* `schema_version` (string, required): Must match supported contract version (currently `"1.0.0"`).
* `base_state_version` (integer, optional): The Digital Twin state version known to the client when the operation was created.
* `client_created_at` (string ISO-8601, required): Client generation timestamp.
* `client_id` (string, required): Identity or callsign of field device/officer.
* `attempt_count` (integer, default 0): Number of sync transmissions attempted by client.

---

## 3. Server Processing Lifecycle & Idempotency

When the server receives a batch of operations at `POST /api/v1/sync`:

```
Client Operation
       │
       ▼
1. Authentication & RBAC Check (X-Actor-Id, X-Actor-Role)
       │
       ▼
2. Schema & Envelope Validation (schema_version == "1.0.0")
       │
       ▼
3. Compute Request Payload Hash: SHA-256(canonical_json(payload))
       │
       ▼
4. Check Idempotency Store
   ├─► Matches operation_id AND request_hash:
   │   └─► Return cached response with status: DUPLICATE (No domain mutation)
   │
   ├─► Matches operation_id BUT request_hash differs:
   │   └─► REJECT with code: IDEMPOTENCY_KEY_REUSE (Conflict)
   │
   └─► First time operation_id seen:
       │
       ▼
5. Optimistic Concurrency & Conflict Evaluation
   ├─► Version check (base_state_version vs current Digital Twin state_version)
   ├─► Lifecycle state check (valid transition in IncidentStateMachine)
   │
   ├─► Incompatible change detected:
   │   └─► Return status: CONFLICT with current server state & diff
   │
   └─► Valid:
       │
       ▼
6. Domain Transaction Execution
   ├─► Apply to IncidentService / FacilityService
   ├─► Emit event to Digital Twin (advancing state_version)
   │
   ▼
7. Store Idempotency Record & Append to Sync Event Ledger
   │
   ▼
8. Return Operation Result (status: ACCEPTED, server_state_version)
```

---

## 4. Response Status Codes & Semantics

| Status | Meaning | Client Action |
| :--- | :--- | :--- |
| `ACCEPTED` | Operation successfully validated and committed to authoritative state. | Mark local record `SYNCED`; remove or archive outbox entry. |
| `DUPLICATE` | Operation was previously processed successfully. Response contains original result. | Mark local record `SYNCED`; clear from active outbox. |
| `CONFLICT` | State version mismatch or incompatible concurrent change. | Keep local record; mark status `CONFLICT`; prompt user/operator for resolution. |
| `REJECTED` | Permanent error (invalid schema, unauthorized, forbidden lifecycle transition). | Mark local record `SYNC_ERROR`; do NOT retry automatically. |
| `RETRYABLE_ERROR` | Transient server error (rate limited, temporary DB lock, network timeout). | Keep in outbox; schedule exponential backoff retry. |

---

## 5. Retry Backoff Policy
Clients encountering network failures or 5xx/429/408 HTTP errors execute bounded exponential backoff:
$$\text{delay} = \min(\text{max\_delay}, \text{base\_delay} \times 2^{\text{attempt}}) + \text{jitter}$$
* `base_delay`: 1,000 ms
* `max_delay`: 30,000 ms
* `max_attempts`: 5
* `jitter`: Uniform random between 0 and 500 ms

---

## 6. Multi-Client & Concurrency Safety
* **Client Lock**: Field PWA acquires a Web Lock via `navigator.locks.request('nexus_field_sync_lock')` to prevent multiple tabs or background workers from executing simultaneous sync sweeps.
* **Server Lock**: Operations targeting the same entity are processed sequentially within an atomic unit.
