# NEXUS AI Failure Modes & Mitigation Protocols

This specification catalogs potential failure modes for machine learning and risk inference pipelines, detailing detection mechanisms and system fallback responses.

---

## 1. Input Failure Modes

| Failure Mode | Root Cause | System Detection | System Response |
| :--- | :--- | :--- | :--- |
| **Negative Rainfall** | Sensor telemetry malfunction or corrupted packet | Pydantic validation (`ge=0.0`) | Rejects payload immediately with HTTP 400 (`validation_error`). Does not clamp silently. |
| **Temporal Inconsistency** | $1\text{-hour rainfall} > 24\text{-hour rainfall}$ | Cross-field model validator | Rejects record with explanatory error. |
| **Out-of-Bounds Coordinates** | Lat/Lon outside $[-90, 90]$ or $[-180, 180]$ | Coordinate validator | Raises `InvalidCoordinateError` (HTTP 400). |
| **Missing Crucial Predictor** | Offline station missing rainfall or elevation | Preprocessor check | Uses training median imputation and attaches warning tag in prediction response. |
| **Unseen Out-of-Distribution Inputs** | Rainfall exceeds physical limits ($>500\text{ mm/hr}$) | Range validator | Rejects input to prevent wild log-odds extrapolation. |

---

## 2. Pipeline & Operational Failure Modes

1. **Uncalibrated Model Extrapolation**:
   When environmental features sit far in the distribution tails, standard linear models can report extreme probabilities ($0.999$ or $0.001$). The UI displays standardized feature contributions so operators see which variable caused the extreme shift.
2. **Offline Inference Fallback**:
   If the API backend is unreachable, the Command Center UI and Field PWA fall back to spatial distance heuristics and physical flood polygon intersection layers instead of failing completely.
3. **No Zero Default on Failure**:
   If an inference calculation fails, the system returns `status: "PREDICTION_UNAVAILABLE"`. It NEVER substitutes `0.0`, ensuring absence of information is never misinterpreted as low danger.

---

## 3. Explainability & Uncertainty Failure Modes

| Failure Mode | Root Cause | System Detection | System Response |
| :--- | :--- | :--- | :--- |
| **Explanation Unavailable** | Missing model explainer or corrupted weights | `RuntimeError` during explanation initialization | Returns HTTP 500 with descriptive error; prediction is still preserved. |
---

## 4. Human Approval & Governance Failure Modes (Phase 21)

| Failure Mode | Root Cause | System Detection | System Response |
| :--- | :--- | :--- | :--- |
| **Approval Race Condition** | Multiple coordinators concurrently approve/reject same recommendation | Thread-locking + state machine validation | Only the first transition succeeds; second request receives `HTTP 400 Bad Request` (`InvalidStateTransitionError`). |
| **Stale State Approval** | Digital Twin state advances while coordinator is reviewing recommendation | `source_state_version != current_state_version` check | Automatically marks recommendation as `EXPIRED` and blocks approval with `HTTP 409 Conflict` (`RECOMMENDATION_STALE`). |
| **Unauthorized Action** | Operator or viewer role attempts to approve or reject | Server-side RBAC permission check | Rejects request with `HTTP 403 Forbidden` and appends `APPROVAL_BLOCKED` audit event. |
| **Precondition Invalidation** | Target hospital becomes full/closed or incident resolves | External service status and capacity query | Marks recommendation as `EXPIRED` and raises `PreconditionFailedError` (HTTP 400). |
| **Simulation Confusion** | Coordinator attempts to approve a What-If simulation recommendation | Mode tag check (`mode == "SIMULATION"`) | Rejects approval with `PreconditionFailedError`, preventing synthetic scenarios from mutating real-world dispatch. |
| **Audit Write Failure** | Storage error during decision recording | Atomic transaction block | State transition is rolled back; approval fails cleanly rather than persisting un-audited operational actions. |

