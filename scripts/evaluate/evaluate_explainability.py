"""
Evaluation script for Phase 19 Explainability, Calibration, and Uncertainty.
Generates:
1. evaluation/results/tables/feature_importance.csv
2. evaluation/results/tables/calibration_metrics.csv
3. evaluation/results/tables/counterfactual_examples.csv
"""

import sys
from pathlib import Path
import joblib
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.explainability.confidence.calibration import RiskProbabilityCalibrator
from ml.explainability.contracts import CalibrationMethod
from ml.explainability.counterfactual.sensitivity import CounterfactualSensitivityEngine
from ml.explainability.feature_attribution.logistic import LogisticRegressionExplainer
from ml.explainability.feature_attribution.tree_ensemble import GradientBoostingExplainer
from ml.risk_model.contracts import RiskFeatureRecord

DATA_PATH = ROOT_DIR / "ml" / "risk_model" / "data" / "reference_flood_risk_dataset.csv"
ARTIFACTS_DIR = ROOT_DIR / "ml" / "risk_model" / "artifacts"
RESULTS_DIR = ROOT_DIR / "evaluation" / "results" / "tables"


def run_explainability_evaluation():
    print("==> Starting Phase 19 Explainability & Calibration Evaluation...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load models
    lr_path = ARTIFACTS_DIR / "baseline_logistic_regression_v1.joblib"
    gb_path = ARTIFACTS_DIR / "gradient_boosting_v1.joblib"

    lr_model = joblib.load(lr_path)
    gb_model = joblib.load(gb_path)

    # 2. Generate Global Feature Importance Table
    lr_explainer = LogisticRegressionExplainer(lr_model)
    gb_explainer = GradientBoostingExplainer(gb_model)

    lr_global = lr_explainer.explain_global()
    gb_global = gb_explainer.explain_global()

    feat_rows = []
    for sig in lr_global.signals:
        feat_rows.append({
            "model_version": lr_model.model_version,
            "algorithm": "LogisticRegression",
            "feature_name": sig.feature_name,
            "display_name": sig.display_name,
            "importance_or_weight": sig.importance_or_weight,
            "rank": sig.rank,
            "unit": sig.unit,
        })
    for sig in gb_global.signals:
        feat_rows.append({
            "model_version": gb_model.model_version,
            "algorithm": "GradientBoostingClassifier",
            "feature_name": sig.feature_name,
            "display_name": sig.display_name,
            "importance_or_weight": sig.importance_or_weight,
            "rank": sig.rank,
            "unit": sig.unit,
        })

    feat_df = pd.DataFrame(feat_rows)
    feat_df.to_csv(RESULTS_DIR / "feature_importance.csv", index=False)
    print(f"    Saved feature importance rankings to {RESULTS_DIR / 'feature_importance.csv'}")

    # 3. Evaluate Calibration on Validation Split
    df = pd.read_csv(DATA_PATH).sort_values(by=["timestamp", "sample_id"]).reset_index(drop=True)
    n = len(df)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    val_df = df.iloc[n_train : n_train + n_val].copy()
    test_df = df.iloc[n_train + n_val :].copy()

    # Fit Platt calibrators on validation split
    lr_calibrator = RiskProbabilityCalibrator(lr_model, lr_model.preprocessor, method=CalibrationMethod.PLATT_SCALING)
    lr_calibrator.fit_on_validation(val_df)

    gb_calibrator = RiskProbabilityCalibrator(gb_model, gb_model.preprocessor, method=CalibrationMethod.PLATT_SCALING)
    gb_calibrator.fit_on_validation(val_df)

    calib_rows = [
        {
            "model_version": lr_model.model_version,
            "calibration_method": "Platt Scaling (Sigmoid)",
            "raw_validation_brier": lr_calibrator.raw_validation_brier,
            "calibrated_validation_brier": lr_calibrator.validation_brier,
            "calibrated_validation_ece": lr_calibrator.validation_ece,
        },
        {
            "model_version": gb_model.model_version,
            "calibration_method": "Platt Scaling (Sigmoid)",
            "raw_validation_brier": gb_calibrator.raw_validation_brier,
            "calibrated_validation_brier": gb_calibrator.validation_brier,
            "calibrated_validation_ece": gb_calibrator.validation_ece,
        },
    ]
    calib_df = pd.DataFrame(calib_rows)
    calib_df.to_csv(RESULTS_DIR / "calibration_metrics.csv", index=False)
    print(f"    Saved calibration benchmark to {RESULTS_DIR / 'calibration_metrics.csv'}")

    # 4. Generate Counterfactual Sensitivity Examples on Sample Test Points
    cf_lr_engine = CounterfactualSensitivityEngine(lr_model)
    cf_gb_engine = CounterfactualSensitivityEngine(gb_model)

    cf_rows = []
    for idx, row in test_df.head(5).iterrows():
        rec = RiskFeatureRecord(
            sample_id=str(row["sample_id"]),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            rainfall_mm_1h=float(row["rainfall_mm_1h"]),
            rainfall_mm_24h=float(row["rainfall_mm_24h"]),
            elevation_m=float(row["elevation_m"]),
            distance_to_river_m=float(row["distance_to_river_m"]),
            slope_degrees=float(row["slope_degrees"]),
            road_density_km=float(row["road_density_km"]),
            infrastructure_exposure_count=int(row["infrastructure_exposure_count"]),
        )
        cf_res = cf_lr_engine.find_counterfactual(rec)
        if cf_res:
            mod_feats = "; ".join(f"{m.display_name}: {m.current_value} -> {m.suggested_value} ({m.delta:+g} {m.unit})" for m in cf_res.modified_features)
            cf_rows.append({
                "sample_id": rec.sample_id,
                "model_version": lr_model.model_version,
                "current_probability": cf_res.current_probability,
                "target_probability": cf_res.target_probability,
                "probability_delta": cf_res.probability_delta,
                "modifications": mod_feats,
                "method": cf_res.method,
            })

    cf_df = pd.DataFrame(cf_rows)
    cf_df.to_csv(RESULTS_DIR / "counterfactual_examples.csv", index=False)
    print(f"    Saved counterfactual examples to {RESULTS_DIR / 'counterfactual_examples.csv'}")
    print("==> Explainability evaluation completed successfully.")


if __name__ == "__main__":
    run_explainability_evaluation()
