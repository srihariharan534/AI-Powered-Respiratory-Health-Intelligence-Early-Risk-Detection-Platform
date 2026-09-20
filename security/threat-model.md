# NEXUS Threat Model (STRIDE Assessment) — Phase 32

## 1. System Scope
NEXUS manages safety-critical municipal emergency data, flood simulations, AI recommendation workflows, and field responder telemetry. Compromise of integrity or availability directly affects human safety.

## 2. Threat Analysis (STRIDE)

| Threat Category | Potential Attack Vector | NEXUS Architectural Mitigation |
| :--- | :--- | :--- |
| **Spoofing Identity** | Attacker impersonates field officer or commander to submit fake incidents or unauthorized approvals. | Server-side RBAC validation (`AuthenticatedActor`, `X-Actor-Id`, `X-Actor-Role`). Client-side identities are never trusted unconditionally. |
| **Tampering with Data** | Attacker alters operation payload between retries to hijack an authorized operation ID. | Deterministic SHA-256 payload hashing (`IDEMPOTENCY_KEY_REUSE` detection in `IdempotencyStore`). Offline IndexedDB isolation. |
| **Repudiation** | Operator denies authorizing an emergency reroute or resource dispatch. | Append-only immutable audit ledgers (`AuditLedger`, `SyncEventLedger`) recording actor, timestamps, state version, and rationale. |
| **Information Disclosure** | Leakage of PII, patient medical status, or vulnerable facility rosters. | Anonymized sender references in SMS gateway, segregated vulnerability layers, strict CORS, non-root containers. |
| **Denial of Service** | Flooding backend with bulk synchronization batches or malformed SMS messages. | Strict length limits (160 chars for SMS, 100 max ops per sync batch), bounded exponential backoff with jitter. |
| **Elevation of Privilege** | Field responder attempts to approve high-risk operational recommendations. | Explicit state machine enforcement (`RecommendationStateMachine` rejects unprivileged roles with 403 Forbidden). |

## 3. Data Flow Boundaries
- **Untrusted / Hostile Boundary**: Public cellular network (SMS fallback gateway). Sanitized via `SMSParser` tokenization, bounds checks, and regex matching before domain ingestion.
- **Controlled Client Boundary**: Field PWA running in browser. Uses Web Locks API to isolate tabs; durable storage managed strictly via IndexedDB with no plain-text secret storage.
- **Trusted Internal Core**: FastAPI API, Digital Twin State Manager, and ML pipelines running in non-root Docker containers.
