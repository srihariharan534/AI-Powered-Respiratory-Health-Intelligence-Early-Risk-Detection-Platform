# NEXUS Audit Ledger & Provenance Specification

## 1. Immutability Guarantee

The NEXUS Audit Ledger is an append-only, chronologically ordered event repository. Under no circumstances may historical audit records be modified or deleted via application APIs.

---

## 2. Event Structure

Every recorded governance event adheres to the canonical `RecommendationAuditEvent` schema:

```json
{
  "audit_event_id": "AUD-e89a1b027c4d",
  "event_type": "RECOMMENDATION_APPROVED",
  "timestamp": "2026-09-20T07:20:10Z",
  "actor_id": "USR-CMD-01",
  "actor_role": "COMMANDER",
  "recommendation_id": "REC-PRIO-INC-001",
  "previous_state": "PENDING",
  "new_state": "APPROVED",
  "reason": "Authorized rescue dispatch based on verified route corridor availability",
  "source_state_version": "state-v104",
  "current_state_version": "state-v104",
  "target_snapshot": {
    "action": "DISPATCH_RESCUE",
    "priority": 1,
    "confidence": 0.88
  }
}
```

---

## 3. Supported Event Types

- `RECOMMENDATION_CREATED`: Logged when an operational proposal is synthesized.
- `RECOMMENDATION_VIEWED`: Logged when an authorized operator inspects a recommendation.
- `RECOMMENDATION_APPROVED`: Logged upon successful human authorization.
- `RECOMMENDATION_REJECTED`: Logged upon operational rejection with mandatory rationale.
- `RECOMMENDATION_EXPIRED`: Logged when a recommendation is invalidated due to state progression.
- `APPROVAL_BLOCKED`: Logged when an unauthorized or stale approval attempt is thwarted.
