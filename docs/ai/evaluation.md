# NEXUS Risk Model Evaluation Specification

This document details the rigorous evaluation protocol, train/test partition integrity, leakage controls, and reproducible results for machine learning risk models in NEXUS.

---

## 1. Evaluation Protocol & Split Strategy

To guarantee zero data leakage and fair comparative benchmarking:
1. **Identical Holdout**: Both Phase 17 Logistic Regression and Phase 18 Gradient Boosting are trained and evaluated on the exact same dataset splits:
   - **Train**: 70% ($N=350$, Positive Rate: 16.0%)
   - **Validation**: 15% ($N=75$, Positive Rate: 20.0%)
   - **Test Holdout**: 15% ($N=75$, Positive Rate: 22.7%)
2. **Deterministic Partitioning**: Partition boundaries are sorted by temporal timestamp and unique `sample_id` before partitioning.
3. **No Target Leakage**: Feature engineering and standardization scaling parameters ($\mu_j, \sigma_j$) and median imputations are computed strictly on the training partition. The test holdout is never seen during preprocessing fitting.

---

## 2. Quantitative Comparative Benchmark Results

All metrics below are generated directly by executable benchmark code (`scripts/evaluate/evaluate_risk_models.py` and `scripts/train/train_gradient_boosting.py`) and recorded in `evaluation/results/tables/model_comparison.csv`:

| Evaluation Dimension | Naive Majority Baseline | Phase 17 Logistic Regression | Phase 18 Gradient Boosting |
| :--- | :--- | :--- | :--- |
| **Model Version** | `naive-majority-class` | `baseline-logistic-regression-v1` | `gradient-boosting-v1` |
| **Algorithm Family** | Trivial Constant | Linear Additive Log-Odds | Non-linear Tree Ensemble (100 estimators) |
| **Test Accuracy** | 77.33% | **94.67%** | 89.33% |
| **Precision** | 0.00% | **100.00%** | **100.00%** |
| **Recall** | 0.00% | **76.47%** | 52.94% |
| **F1-Score** | 0.00% | **86.67%** | 69.23% |
| **ROC-AUC** | 0.5000 | **0.9888** | 0.9594 |
| **PR-AUC** | 0.2267 | **0.9679** | 0.8962 |
| **Brier Score** (Lower is better) | 0.1753 | **0.0412** | 0.0772 |
| **Expected Calibration Error** | 0.0000 | **0.1016** | 0.1958 |
| **Inference Latency (Mean)** | 0.000 ms | 0.035 ms | **0.024 ms** |

---

## 3. Evidence-Based Model Selection Analysis

The comparative evaluation provides clear empirical evidence:
- **Accuracy & F1 Advantage**: The Phase 17 Logistic Regression baseline demonstrates superior classification performance over Gradient Boosting ($94.7\%$ vs $89.3\%$ accuracy, and $86.7\%$ vs $69.2\%$ F1-score).
- **Probability Quality & Calibration**: Logistic Regression exhibits lower Brier score ($0.0412$ vs $0.0772$) and lower Expected Calibration Error ($0.1016$ vs $0.1958$), indicating that its probability outputs are significantly more reliable for emergency risk assessment.
- **Operational Conclusion**: Rather than prematurely declaring the more complex non-linear ensemble the winner, **the Phase 17 linear baseline remains the recommended default model**. Gradient Boosting is preserved in the local model registry as an alternative non-linear option accessible via `POST /api/v1/risk/predict?model_version=gradient-boosting-v1`.
