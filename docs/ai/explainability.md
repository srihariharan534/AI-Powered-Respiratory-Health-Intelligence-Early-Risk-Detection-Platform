# NEXUS AI Explainability & Uncertainty Architecture (Phase 19)

This specification details the mathematical definitions, contracts, runtime implementation, and operational boundaries of the Explainability, Calibration, Uncertainty, and Counterfactual layer in NEXUS.

---

## 1. Operating Principles

1. **Non-Causal Explanation**:
   Attributions describe how input predictors influenced the internal calculations of the model. They must **never** be presented as physical causality.
   - *Allowed*: "Terrain elevation was associated with lower predicted flood risk in this model."
   - *Forbidden*: "Elevated terrain prevents flood inundation."
2. **Strict Additive Reconstruction**:
   Linear models must mathematically satisfy:
   $$\text{logit}(p) = w_0 + \sum_{j=1}^M (w_j \cdot z_j)$$
   where $w_0$ is the intercept, $w_j$ is the standardized coefficient, and $z_j = (x_j - \mu_j)/\sigma_j$.
3. **Prevention of Calibration Leakage**:
   Calibration transformations (Platt scaling / Sigmoid and Isotonic regression) are trained strictly on validation partitions ($N=45$) and never on the held-out test split ($N=75$).
4. **Data Quality vs. Model Uncertainty**:
   Missing inputs or imputed values are reported as **Data Quality** issues, separate from **Distribution Distance (OOD)** and **Calibration Error**.

---

## 2. Feature Attribution Pipeline

### 2.1 Baseline Logistic Regression (`baseline-logistic-regression-v1`)
- **Output Space**: $\text{LOG\_ODDS}$
- **Base Value**: $w_0 = -0.5843$ (intercept)
- **Local Attribution**: $c_j = w_j \cdot z_j$
- **Directional Classification**:
  - $c_j > +0.02 \implies \text{INCREASES\_RISK}$
  - $c_j < -0.02 \implies \text{DECREASES\_RISK}$
  - $|c_j| \le 0.02 \implies \text{NEUTRAL}$

### 2.2 Gradient Boosting (`gradient-boosting-v1`)
- **Output Space**: $\text{PROBABILITY\_MARGIN}$
- **Base Value**: $0.0$ (neutral baseline margin)
- **Local Attribution**: $c_j = I_j \cdot z_j \cdot s_j$, where $I_j$ is the Gini impurity decrease, $z_j$ is the standardized feature deviation, and $s_j \in \{-1, +1\}$ is the physical risk gradient.
- **Global Ranking**: Gini impurity decrease summing to $1.0$ across all 100 shallow trees.

---

## 3. Global Feature Signals (Empirical Benchmark)

From `evaluation/results/tables/feature_importance.csv`:

| Rank | Baseline Logistic Regression (Standardized Weight) | Gradient Boosting (Gini Impurity Importance) | Physical Unit |
| :---: | :--- | :--- | :---: |
| 1 | **Terrain Elevation** ($-2.5844$) | **24-Hour Cumulative Rainfall** ($44.38\%$) | meters / mm |
| 2 | **24-Hour Rainfall** ($+2.4647$) | **Distance to River/Drainage** ($23.35\%$) | mm / meters |
| 3 | **Distance to River** ($-2.1759$) | **Terrain Elevation** ($20.86\%$) | meters |
| 4 | **1-Hour Rainfall** ($+1.0335$) | **1-Hour Rainfall** ($4.95\%$) | mm |
| 5 | **Road Density** ($+0.6123$) | **Topographic Slope** ($3.74\%$) | $\text{km}/\text{km}^2$ |
| 6 | **Topographic Slope** ($-0.4660$) | **Road Density** ($2.24\%$) | degrees |
| 7 | **Facility Exposure** ($+0.2221$) | **Facility Exposure** ($0.47\%$) | facilities |

---

## 4. Probability Calibration (Empirical Validation Results)

From `evaluation/results/tables/calibration_metrics.csv` evaluated on validation partition:

| Model Version | Calibration Method | Raw Validation Brier | Calibrated Validation Brier | Validation ECE |
| :--- | :--- | :---: | :---: | :---: |
| `baseline-logistic-regression-v1` | Platt Scaling (Sigmoid) | **0.0444** | 0.0648 | 0.2605 |
| `gradient-boosting-v1` | Platt Scaling (Sigmoid) | **0.0585** | 0.0787 | 0.2482 |

> **Finding**: On this well-regularized dataset, the raw probabilities of the L2 logistic regression baseline already exhibit superior calibration (raw Brier $0.0444$) compared to post-hoc Platt scaling ($0.0648$). Both raw and calibrated estimates are reported with validation metrics to ensure full transparency.

---

## 5. Uncertainty & Out-of-Distribution (OOD) Diagnostics

Under standardized feature space $z \sim \mathcal{N}(0, \mathbf{I}_7)$, the Euclidean distance from the training centroid is:
$$D = \sqrt{\sum_{j=1}^7 z_j^2}$$

- **Status `IN_DISTRIBUTION`** ($D \le 3.2$): Observation resides within the regular training envelope.
- **Status `WARNING`** ($3.2 < D \le 4.8$): Unusual combination or high-consequence edge observation.
- **Status `OUT_OF_DISTRIBUTION`** ($D > 4.8$): Extreme tail anomaly or sensor telemetry outlier.

---

## 6. Counterfactual Sensitivity

- Uses bounded deterministic search across candidate environmental variables (`rainfall_mm_24h`, `elevation_m`, `distance_to_river_m`).
- Respects hard physical domain boundaries (non-negative rainfall, non-negative river distance, elevation $\ge -50\text{m}$, rainfall $1\text{h} \le 24\text{h}$).
- Reports exact required modifications to flip classification or cross critical triage margins.
- **Notice**: Counterfactual outputs are mathematical sensitivities only, never civil defense instructions.
