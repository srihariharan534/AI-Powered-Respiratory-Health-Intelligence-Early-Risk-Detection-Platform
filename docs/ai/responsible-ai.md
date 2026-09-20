# NEXUS Responsible AI Specification

This document establishes ethical standards, operational safety constraints, and decision boundaries governing artificial intelligence and statistical learning in NEXUS.

---

## 1. Core Operating Principles

1. **Human-in-the-Loop Authority**:
   No machine learning model in NEXUS is permitted to execute autonomous operational actions. Predictions and risk estimates serve exclusively as advisory inputs to District Emergency Operations Center (DEOC) coordinators.
2. **Honesty About Uncertainty & Provenance**:
   System interfaces must never present simulated or synthetic predictions as empirical real-world ground truth. All telemetry and inference responses must maintain explicit data mode tags (`REAL_DATA`, `SIMULATION`, `DEMO`).
3. **Defense Against Cascading Failures**:
   If upstream sensor feeds fail or feature inputs fall outside valid ranges, the system must report `prediction_unavailable` rather than defaulting to `0.0` (which would falsely communicate zero risk).

---

## 2. Risk Distribution & Asymmetric Costs

In flood disaster management, prediction errors have asymmetric human costs:

| Error Type | Operational Consequence | Mitigation in NEXUS |
| :--- | :--- | :--- |
| **False Negative** ($y=1, \hat{y}=0$)<br>Unpredicted Flood Risk | Emergency vehicles enter submerged roads; rescue shelters become cut off without advance preparation. | Low classification threshold options (e.g. 0.35) for precautionary triage; physical exposure tests run alongside ML models. |
| **False Positive** ($y=0, \hat{y}=1$)<br>False Alarm Disruption | Precautionary detours consume fuel and increase transit times; potential evacuation fatigue. | Transparent linear feature attributions show *why* the model estimated high probability, allowing human verification. |

---

## 3. Distribution Shift & Climate Non-Stationarity

1. **Extreme Unprecedented Events**:
   Statistical models trained on historical or synthetic envelopes cannot reliably extrapolate to 500-year flood anomalies or catastrophic structural breaches.
2. **Urban Topography Changes**:
   New road construction, elevated bridges, or stormwater drainage interventions shift runoff characteristics. Models must undergo scheduled re-calibration and version tracking.

---

## 4. Explainability, Uncertainty & Non-Causality

1. **Non-Causal Statistical Association**:
   Attributions and counterfactual sensitivities explain the mathematical calculations inside the model, never physical causes. Interface text must never suggest that artificial feature alterations directly alter real-world hydrological dynamics.
2. **Probability vs. Reliability**:
   A high probability (e.g. $0.95$) does not imply $95\%$ reliability. Probability calibration curves (ECE, Brier score) and data completeness must always be communicated together.
3. **Transparent Uncertainty**:
   Standardized distance from the training distribution is computed and flagged (`IN_DISTRIBUTION`, `WARNING`, `OUT_OF_DISTRIBUTION`) so coordinators know when a model is being evaluated on unprecedented edge conditions.

---

## 6. Operational Recommendation Engine Guardrails (Phase 20)

To ensure high-stakes flood response decisions remain fully accountable, the Operational Recommendation Engine operates under strict constitutional boundaries:
- **Mandatory Human Approval**: Every recommendation enforces `requires_human_approval: true`. Autonomous dispatch, road closure, or evacuation execution is strictly forbidden.
- **State Invalidation (Stale Recommendations)**: Recommendations are explicitly anchored to a digital twin `source_state_version`. Any state transition (e.g. rising flood water or infrastructure degradation) automatically marks pending recommendations as `EXPIRED`. Approving stale recommendations is blocked with `409 Conflict`.
- **Transparent Multi-Factor Scoring**: Recommendations rely on deterministic, policy-versioned scoring functions rather than opaque black boxes. Every recommendation exposes its contributing `factors` and their respective weights.
- **No False Certainty**: Confidence values correspond directly to empirical normalized evaluation scores and include explicit `uncertainty` intervals.
- **Append-Only Decision Ledger**: Operator approvals and rejections require rationales that are immutably preserved in the audit log for disaster after-action reviews.

