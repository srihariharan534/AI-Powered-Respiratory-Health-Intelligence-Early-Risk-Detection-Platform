# NEXUS Operational Flood Risk Modeling Architecture

This document specifies the architectural structure, pipeline flow, and integration boundaries for machine learning risk models across NEXUS.

---

## 1. Architectural Pipeline

```text
DATA INGRESS
  ├── Reference Environmental Observations (ml/risk_model/data/)
  └── Real-time Gauge Feeds & Digital Twin Features (Future Phases)
         ↓
VALIDATION & PREPROCESSING (ml/risk_model/preprocessing.py)
  ├── Pydantic Invariant Bounds (rainfall >= 0, 1h <= 24h, WGS84 range)
  ├── Training-Set Median Imputation
  └── Zero-Mean Unit-Variance Scaling
         ↓
MODEL ENSEMBLE REGISTRY (ml/risk_model/artifacts/)
  ├── Phase 17: Baseline Logistic Regression (Linear Log-Odds)
  └── Phase 18: Gradient Boosting Classifier (Non-linear Tree Ensemble)
         ↓
UNIFIED EVALUATION BENCHMARK (evaluation/results/tables/)
  ├── Comparative Metrics (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC)
  ├── Probability Quality (Brier Score, Expected Calibration Error)
  └── Latency Benchmarking (Mean, Median, P95)
         ↓
OPERATIONAL INFERENCE & API (services/api/app/routes/risk.py)
  ├── Point Prediction: POST /api/v1/risk/predict?model_version=...
  ├── Batch Prediction: POST /api/v1/risk/batch
  ├── Model Metadata: GET /api/v1/risk/model-info?model_version=...
  └── GIS FeatureCollection: POST /api/v1/risk/geojson
         ↓
DECISION SUPPORT INTEGRATION (Phases 19 & 20)
  ├── Phase 19: Local Tree Attribution & Uncertainty Bounds
  └── Phase 20: Human-in-the-Loop Recommendation Proposals
```

---

## 2. Model Registry & Versioning Design

All model artifacts follow deterministic naming and packaging:
- **`ml/risk_model/artifacts/{model_version}.joblib`**: Clean, self-contained binary model artifact.
- **`ml/risk_model/artifacts/{model_version}_metadata.json`**: Accompanies every model with training timestamp, SHA-256 dataset fingerprint, hyperparameters, coefficients / importances, and documented limitations.

---

## 3. Strict Boundary Rules

1. **Advisory Only**: Model outputs are strictly advisory analytical scores. They never trigger automated road closures, facility shutdowns, or team dispatches.
2. **No Training in Request Path**: Inference routes load serialized artifacts; training is exclusively performed offline via CLI commands (`scripts/train/`).
3. **No Uncalibrated Cloud Dependency**: All inference executes locally on offline-first edge or server hardware in under $1\text{ ms}$.
