# NEXUS Privacy & Data Protection Specification (Phase 32)

## 1. Core Principles
1. **Minimization**: Capture only operational telemetry required for life-safety response (WGS84 coordinates, incident description, severity, status).
2. **Anonymization**: Field responders and civilian SMS reporters are referenced via pseudonymous identifiers (e.g. `ANON-RADIO-01`, `FIELD_OFFICER_01`). Phone numbers and IMEI metadata are hashed or stripped at gateway ingestion.
3. **Storage Segregation**: Local IndexedDB offline storage stores operational field records without logging user credentials, session tokens, or personal identifiers.
4. **Audit Immutability**: All decisions and operational dispatches are logged with actor identifiers to guarantee accountability without disclosing civilian private details.
