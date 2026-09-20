# Security Policy — NEXUS

NEXUS handles mission-critical emergency response and infrastructure triage data. Security, confidentiality, and data integrity are essential to operational decision-making.

---

## 1. Supported Versions

| Version | Supported | Notes |
| :--- | :--- | :--- |
| `0.1.x` (Current Prototype / Active) | :white_check_mark: | Active evaluation version |

---

## 2. Reporting a Vulnerability

If you discover a potential vulnerability or security weakness in NEXUS:

1. **Do NOT file a public issue.**
2. Send an advisory report to the security contact / repository maintainers.
3. Include detailed reproduction steps, environment details, and affected components (e.g. `services/sync`, `digital_twin`, API authentication).

We aim to acknowledge reports within 48 hours and provide remediation or mitigation guidelines.

---

## 3. Security Principles in NEXUS

1. **Zero Secrets in Source**: No API tokens, keys, passwords, or credentials may ever be committed to git. All configurations use `.env` patterns governed by `.env.example`.
2. **Auditability**: All state mutations, triage priority approvals, and simulated bridge failures log immutable audit records with timestamps and actor identities.
3. **Idempotency & Replay Protection**: Offline sync endpoints must enforce idempotency keys to prevent double-submission or replay attacks.
4. **Input Validation**: Strict schema enforcement via Pydantic on backend endpoints and sanitized inputs on field client interfaces.
