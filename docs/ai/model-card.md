# NEXUS Model Card: Operational Flood Risk Models

This model card adheres to responsible AI documentation practices and details the intended purpose, data inputs, performance characteristics, and strict operational boundaries of the Phase 17 Baseline Logistic Regression model and the Phase 18 Gradient Boosting model.

---

## 1. Model Overview

| Attribute | Phase 17 Baseline Model | Phase 18 Advanced Nonlinear Model |
| :--- | :--- | :--- |
| **Model Identifier** | `baseline-logistic-regression-v1` | `gradient-boosting-v1` |
| **Algorithm** | L2-Regularized Logistic Regression ($C=1.0$) | Gradient Boosting Classifier (100 estimators, depth=3, lr=0.05) |
| **Framework** | `scikit-learn >= 1.8.0`, `numpy`, `pandas` | `scikit-learn >= 1.8.0`, `numpy`, `pandas` |
| **Decision Surface** | Linear additive log-odds | Ensembles of shallow non-linear decision trees |
| **Target Variable** | `operational_flood_risk` (Binary: 0=nominal, 1=disruption $\ge 15\text{ cm}$) | `operational_flood_risk` (Binary: 0=nominal, 1=disruption $\ge 15\text{ cm}$) |
| **Dataset Fingerprint** | `0094e2f4a251cf1ac24e560e534f76b34ebb8fb9d56923c2bc0c3203dc5ee66c` | `0094e2f4a251cf1ac24e560e534f76b34ebb8fb9d56923c2bc0c3203dc5ee66c` |
| **Provenance Mode** | `SYNTHETIC_SCENARIO_OBSERVATION` | `SYNTHETIC_SCENARIO_OBSERVATION` |

---

## 2. Input Features & Preprocessing

Both models consume the identical 7 standardized predictors ($z_j = (x_j - \mu_j) / \sigma_j$):

| Feature Name | Type | Physical Unit | Valid Range | Mean ($\mu$) | Std ($\sigma$) | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `rainfall_mm_1h` | Float | mm | $[0, 500]$ | Fitted on Train | Fitted on Train | 1-hour accumulated rainfall |
| `rainfall_mm_24h` | Float | mm | $[0, 2000]$ | Fitted on Train | Fitted on Train | 24-hour antecedent precipitation |
| `elevation_m` | Float | meters | $[-50, 9000]$ | Fitted on Train | Fitted on Train | Elevation above mean sea level |
| `distance_to_river_m`| Float | meters | $[0, 100000]$| Fitted on Train | Fitted on Train | Distance to nearest drainage/river channel |
| `slope_degrees` | Float | degrees | $[0, 90]$ | Fitted on Train | Fitted on Train | Topographic slope angle |
| `road_density_km` | Float | $\text{km}/\text{km}^2$| $[0, 50]$ | Fitted on Train | Fitted on Train | Highway/road concentration within 500m |
| `infrastructure_exposure_count` | Int | count | $[0, 100]$ | Fitted on Train | Fitted on Train | Number of facilities (hospitals/shelters) in 1km |

### Preprocessing Protocol
1. **Missing Data Imputation**: Missing values are imputed using feature medians computed strictly on the training partition.
2. **Standardization**: Numerical features are scaled to zero-mean, unit-variance strictly on training observations to prevent data leakage.
3. **Out-of-Distribution Validation**: Inputs outside defined physical bounds (e.g., negative rainfall or invalid coordinates) are rejected at API ingress with HTTP 400.

---

## 3. Side-by-Side Benchmark & Model Selection Evidence

Evaluated on the held-out test partition ($N=75$, Positive Rate: 22.7%):

| Metric | Majority-Class Baseline | Baseline Logistic Regression (Phase 17) | Gradient Boosting (Phase 18) | Finding / Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **Accuracy** | 77.33% | **94.67%** | 89.33% | Baseline achieves higher overall test accuracy |
| **Precision** | 0.00% | **100.00%** | **100.00%** | Both models demonstrate zero false positives on test split |
| **Recall** | 0.00% | **76.47%** | 52.94% | Baseline captures more true positive flood risks |
| **F1-Score** | 0.00% | **86.67%** | 69.23% | Baseline achieves higher F1 balance |
| **ROC-AUC** | 0.5000 | **0.9888** | 0.9594 | Baseline maintains higher discriminative power |
| **PR-AUC** | 0.2267 | **0.9679** | 0.8962 | Baseline achieves higher precision-recall envelope |
| **Brier Score** (Lower is better) | 0.1753 | **0.0412** | 0.0772 | Baseline probabilities are significantly better calibrated |
| **Expected Calibration Error** | 0.0000 | **0.1016** | 0.1958 | Gradient Boosting shows higher overconfidence/calibration error |
| **Mean Inference Latency** | 0.00 ms | **0.035 ms** | **0.024 ms** | Both models provide sub-millisecond offline execution |

### Model Selection Conclusion
> **Neutral Evidence-Based Determination**: On this continuous environmental reference dataset, **Logistic Regression outperforms Gradient Boosting** across accuracy (94.7% vs 89.3%), recall (76.5% vs 52.9%), and probability calibration (Brier: 0.0412 vs 0.0772). The linear baseline remains the primary recommendation, while Gradient Boosting is preserved as an alternative nonlinear tree engine.

---

## 4. Interpretability & Feature Attribution

### Phase 17 Standardized Logistic Coefficients ($\beta_j$)
- `elevation_m`: **-2.5844** (Decreases risk)
- `rainfall_mm_24h`: **+2.4647** (Increases risk)
- `distance_to_river_m`: **-2.1759** (Decreases risk)
- `rainfall_mm_1h`: **+1.0335** (Increases risk)
- `road_density_km`: **+0.6123** (Increases risk)
- `slope_degrees`: **-0.4660** (Decreases risk)
- `infrastructure_exposure_count`: **+0.2221** (Increases risk)

### Phase 18 Gradient Boosting Gini Feature Importances
- `rainfall_mm_24h`: **0.4438 (44.4%)**
- `distance_to_river_m`: **0.2335 (23.4%)**
- `elevation_m`: **0.2086 (20.9%)**
- `rainfall_mm_1h`: **0.0495 (5.0%)**
- `slope_degrees`: **0.0374 (3.7%)**
- `road_density_km`: **0.0224 (2.2%)**
- `infrastructure_exposure_count`: **0.0047 (0.5%)**

> **Important**: Gini importances quantify split purity improvement in the ensemble; they do NOT demonstrate physical causality.

### Phase 19 Explainability, Calibration & Uncertainty Layer
- **Local Attribution**:
  - `baseline-logistic-regression-v1`: Exact log-odds feature attribution satisfying $\text{logit}(p) = w_0 + \sum (w_j \cdot z_j)$.
  - `gradient-boosting-v1`: Tree-leaf probability margin attribution.
- **Probability Calibration**: Platt scaling (sigmoid) and isotonic regression fitted strictly on validation data ($N=45$) with zero test leakage.
- **Uncertainty & OOD Diagnostics**: Standardized centroid distance diagnostic ($D = \sqrt{\sum z_j^2}$) reporting `IN_DISTRIBUTION` ($D \le 3.2$), `WARNING` ($3.2 < D \le 4.8$), and `OUT_OF_DISTRIBUTION` ($D > 4.8$).
- **Counterfactual Sensitivity**: Controlled deterministic parameter perturbation determining the minimal rainfall or elevation shift needed to cross operational classification thresholds while enforcing strict physical domain bounds.

---

## 5. Operational Boundaries & Failure Modes

1. **No Autonomous Dispatch or Action**: Model predictions are strictly advisory. Operational decisions (road closures, evacuations, hospital transfers) require human coordinator authorization.
2. **Synthetic Demonstration Notice**: Datasets are based on scenario observations. Operational certification requires local gauge calibration.
3. **Tree Clamping in Extrapolation**: Tree-based models cannot extrapolate beyond training leaf values. Inputs far outside training distributions return clamped predictions.
4. **Offline Compatibility**: Both models serialize to lightweight `.joblib` files ($<150\text{ KB}$) and execute with zero external cloud or internet connectivity.

