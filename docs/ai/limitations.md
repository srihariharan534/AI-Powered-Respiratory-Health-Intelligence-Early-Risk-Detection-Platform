# NEXUS AI Limitations & Boundary Analysis

This document details the scientific and engineering limitations of the machine learning components in NEXUS, with specific focus on the Phase 17 Baseline Risk Model.

---

## 1. Baseline Model Limitations (`baseline-logistic-regression-v1`)

1. **Association, Not Causality**:
   Logistic regression models statistical correlation between environmental covariates (rainfall, elevation, slope) and operational disruption. It does NOT establish physical hydrodynamic causality.
2. **Linear Log-Odds Boundary**:
   The model assumes an additive, log-linear relationship:
   $$\log\left(\frac{p}{1-p}\right) = \beta_0 + \beta_1 z_1 + \dots + \beta_p z_p$$
   It cannot represent complex interactions (such as backwater ponding where low slope combined with high river stage abruptly triggers flooding even under light rainfall).
3. **Point Probability Estimates**:
   The baseline outputs scalar probabilities without Bayesian posterior intervals or conformal prediction bands. A probability of `0.65` indicates model prediction under the fitted parameters, not calibrated confidence bounds.
4. **Coarse Spatial Aggregation**:
   Features are sampled at point coordinates. Micro-topographic features (curbs, drainage inlets, local walls) smaller than the spatial sampling grid are unresolved.

---

## 2. Data Limitations

1. **Synthetic Nature of Baseline Reference Dataset**:
   The current reference dataset (`reference_flood_risk_dataset.csv`) is generated via deterministic scenario synthesis to allow offline pipeline verification. It must not be marketed as real-world validated truth.
2. **Missing Sensor Telemetry**:
   In offline or degraded field conditions, live rainfall gauges or river level sensors may be unavailable. The model must rely on fallback defaults or flag predictions as degraded.

---

## 3. Operational Recommendation & Governance Limitations (Phase 21)

1. **Human Approval Does Not Guarantee Operational Success**:
   An incident commander's authorization records an operational decision based on the best available situational snapshot. Real-world conditions (such as sudden flash floods, unmapped debris, or power outages) may still alter outcomes on the ground.
2. **Recommendation Quality Inherits Upstream Data Bounds**:
   Recommendations are only as accurate as the Digital Twin state, road graph accessibility tags, and hospital telemetry inputs. Obsolete or unverified field reports degrade recommendation viability.
3. **State Version Invalidation Window**:
   High-frequency state mutations (e.g. rapid sensor updates) will frequently expire pending recommendations. Coordinators in fast-moving flood events must regenerate proposals against the newest state version.
4. **Audit Records Track System Events, Not Ground Truth**:
   The immutable audit ledger certifies what decisions were taken inside NEXUS, by whom, at what timestamp, and under what version. It does not provide cryptographic proof of physical field team movements.
