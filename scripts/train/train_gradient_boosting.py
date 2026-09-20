"""
Deterministic Training Script for Gradient Boosting Flood Risk Model (Phase 18).
Usage:
    python scripts/train/train_gradient_boosting.py

Operations:
1. Loads documented reference dataset.
2. Computes SHA-256 dataset fingerprint for exact provenance tracing.
3. Splits into Train (70%), Validation (15%), Test (15%) splits (same seed/ordering as Phase 17).
4. Fits RiskFeaturePreprocessor on Train split.
5. Fits GradientBoostingRiskModel.
6. Evaluates model on Test split (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Brier score, ECE).
7. Benchmarks inference latency (mean, median, p95).
8. Saves model artifact (.joblib) and metadata JSON to ml/risk_model/artifacts/.
9. Updates comparative benchmark table in evaluation/results/tables/model_comparison.csv and headline_metrics.csv.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.risk_model.baseline.logistic_regression.evaluation import (
    evaluate_risk_predictions,
)
from ml.risk_model.contracts import ModelMetadata, RiskFeatureRecord
from ml.risk_model.gradient_boosting.model import (
    GradientBoostingRiskModel,
    compute_dataset_fingerprint,
)
from ml.risk_model.preprocessing import FEATURE_COLUMNS, RiskFeaturePreprocessor

DATA_PATH = ROOT_DIR / "ml" / "risk_model" / "data" / "reference_flood_risk_dataset.csv"
ARTIFACTS_DIR = ROOT_DIR / "ml" / "risk_model" / "artifacts"
RESULTS_DIR = ROOT_DIR / "evaluation" / "results" / "tables"


def train_gradient_boosting(
    data_path: Path = DATA_PATH,
    artifacts_dir: Path = ARTIFACTS_DIR,
    results_dir: Path = RESULTS_DIR,
    random_seed: int = 42,
) -> GradientBoostingRiskModel:
    """Trains the Gradient Boosting risk model."""
    print(f"==> Loading reference risk dataset from: {data_path}")
    if not data_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. Run ml/risk_model/data/generator.py first."
        )

    # 1. Dataset Fingerprint
    fingerprint = compute_dataset_fingerprint(data_path)
    print(f"    Dataset SHA-256 Fingerprint: {fingerprint}")

    df = pd.read_csv(data_path)
    print(f"    Loaded {len(df)} records.")

    # 2. Split into Train (70%), Validation (15%), Test (15%) deterministically
    df = df.sort_values(by=["timestamp", "sample_id"]).reset_index(drop=True)
    n = len(df)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)

    train_df = df.iloc[:n_train].copy()
    val_df = df.iloc[n_train : n_train + n_val].copy()
    test_df = df.iloc[n_train + n_val :].copy()

    print(f"    Split: Train={len(train_df)} ({train_df['operational_flood_risk'].mean():.1%} pos), "
          f"Val={len(val_df)} ({val_df['operational_flood_risk'].mean():.1%} pos), "
          f"Test={len(test_df)} ({test_df['operational_flood_risk'].mean():.1%} pos)")

    # 3. Fit Preprocessor strictly on Train split
    preprocessor = RiskFeaturePreprocessor(feature_columns=FEATURE_COLUMNS)
    preprocessor.fit(train_df)

    # 4. Train Gradient Boosting Model
    model = GradientBoostingRiskModel(
        model_version="gradient-boosting-v1",
        n_estimators=100,
        learning_rate=0.05,
        max_depth=3,
        min_samples_split=4,
        min_samples_leaf=2,
        subsample=0.85,
        random_state=random_seed,
    )
    t0 = time.perf_counter()
    model.fit(train_df, preprocessor, target_col="operational_flood_risk")
    train_duration_sec = time.perf_counter() - t0
    print(f"    Trained GradientBoostingClassifier in {train_duration_sec:.3f} seconds.")

    # 5. Evaluate on Test Split
    y_test = test_df["operational_flood_risk"].values
    y_prob = model.predict_proba(test_df)
    metrics = evaluate_risk_predictions(y_test, y_prob)

    print("\n==> Evaluation Metrics on Test Partition (Gradient Boosting):")
    print(f"    Accuracy: {metrics['accuracy']:.4f}")
    print(f"    Precision: {metrics['precision']:.4f}")
    print(f"    Recall: {metrics['recall']:.4f}")
    print(f"    F1 Score: {metrics['f1_score']:.4f}")
    print(f"    ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"    PR-AUC: {metrics['pr_auc']:.4f}")
    print(f"    Brier Score: {metrics['brier_score']:.4f}")
    print(f"    Expected Calibration Error (ECE): {metrics['expected_calibration_error']:.4f}")

    # 6. Feature Importances (Gini Impurity Decrease)
    importances = model.get_feature_importances()
    print("\n==> Feature Importances (Gini Impurity Reduction):")
    for feat, imp in sorted(importances.items(), key=lambda x: x[1], reverse=True):
        print(f"    {feat:30s}: {imp:.4f} ({imp*100:.1f}%)")

    # 7. Benchmark Single & Batch Latency
    sample_record = RiskFeatureRecord(
        sample_id="BENCHMARK-001",
        latitude=13.0827,
        longitude=80.2707,
        rainfall_mm_1h=15.0,
        rainfall_mm_24h=60.0,
        elevation_m=4.2,
        distance_to_river_m=120.0,
        slope_degrees=1.1,
        road_density_km=5.0,
        infrastructure_exposure_count=2,
    )

    latencies_ms = []
    for _ in range(50):
        t_start = time.perf_counter()
        model.predict_single(sample_record)
        latencies_ms.append((time.perf_counter() - t_start) * 1000.0)

    latency_summary = {
        "mean_latency_ms": round(float(np.mean(latencies_ms)), 3),
        "median_latency_ms": round(float(np.median(latencies_ms)), 3),
        "p95_latency_ms": round(float(np.percentile(latencies_ms, 95)), 3),
    }
    print(f"\n==> Inference Latency Benchmark (50 iterations):")
    print(f"    Mean: {latency_summary['mean_latency_ms']} ms | Median: {latency_summary['median_latency_ms']} ms | P95: {latency_summary['p95_latency_ms']} ms")

    # 8. Load baseline comparison from Phase 17 metadata if present
    baseline_metadata_path = artifacts_dir / "baseline_logistic_regression_v1_metadata.json"
    comparison_info = {}
    if baseline_metadata_path.is_file():
        with open(baseline_metadata_path, "r", encoding="utf-8") as f:
            base_meta = json.load(f)
            comparison_info = {
                "baseline_model_version": base_meta["model_version"],
                "baseline_accuracy": base_meta["metrics"]["accuracy"],
                "baseline_f1": base_meta["metrics"]["f1_score"],
                "baseline_roc_auc": base_meta["metrics"]["roc_auc"],
                "baseline_brier_score": base_meta["metrics"]["brier_score"],
            }

    # 9. Create Model Metadata
    metadata = ModelMetadata(
        model_id="NEXUS-RISK-GB-001",
        model_version=model.model_version,
        algorithm="Gradient Boosting Classifier (100 estimators, max_depth=3, lr=0.05)",
        target_definition="Binary operational disruption/inundation >= 15cm (0=nominal, 1=risk)",
        training_dataset_id="reference_flood_risk_dataset_v1",
        dataset_mode="SYNTHETIC_SCENARIO_OBSERVATION",
        dataset_fingerprint=fingerprint,
        feature_names=FEATURE_COLUMNS,
        feature_importances=importances,
        hyperparameters=model.hyperparameters,
        metrics={**metrics, **latency_summary, "train_duration_sec": round(train_duration_sec, 3)},
        comparison_to_baseline=comparison_info,
        training_timestamp=datetime.now(timezone.utc).isoformat(),
        random_seed=random_seed,
        limitations=[
            "Non-linear decision tree ensemble; leaves are clamped to empirical partition ranges.",
            "Feature importances indicate predictive contribution in tree splits, NOT physical causality.",
            "Dataset is based on synthetic scenario observations; field sensor validation required before operational deployment.",
            "Does NOT decide evacuation priority, road closures, or dispatch rescue teams.",
        ],
    )
    model.metadata = metadata

    # 10. Save Artifacts
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifacts_dir / "gradient_boosting_v1.joblib"
    joblib.dump(model, model_path)

    metadata_path = artifacts_dir / "gradient_boosting_v1_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=2)

    # 11. Update model_comparison.csv
    comparison_csv = results_dir / "model_comparison.csv"
    existing_df = pd.read_csv(comparison_csv) if comparison_csv.is_file() else pd.DataFrame()

    gb_row = {
        "model_version": model.model_version,
        "algorithm": "Gradient Boosting (Non-linear Trees)",
        "test_samples": metrics["sample_count"],
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1_score": metrics["f1_score"],
        "roc_auc": metrics["roc_auc"],
        "pr_auc": metrics["pr_auc"],
        "brier_score": metrics["brier_score"],
        "ece": metrics["expected_calibration_error"],
        "dataset_mode": metadata.dataset_mode,
        "timestamp": metadata.training_timestamp,
    }

    # Filter out previous row for this model_version if exists
    if not existing_df.empty and "model_version" in existing_df.columns:
        filtered_df = existing_df[existing_df["model_version"] != model.model_version]
        updated_df = pd.concat([filtered_df, pd.DataFrame([gb_row])], ignore_index=True)
    else:
        updated_df = pd.DataFrame([gb_row])

    updated_df.to_csv(comparison_csv, index=False)

    # 12. Update headline_metrics.csv
    headline_csv = results_dir / "headline_metrics.csv"
    headline_rows = [
        {
            "benchmark": "Phase 17 Baseline Logistic Regression",
            "primary_metric": "roc_auc",
            "baseline_value": 0.5000,
            "model_value": comparison_info.get("baseline_roc_auc", 0.9888),
            "brier_score": comparison_info.get("baseline_brier_score", 0.0412),
            "timestamp": metadata.training_timestamp,
        },
        {
            "benchmark": "Phase 18 Gradient Boosting Risk Model",
            "primary_metric": "roc_auc",
            "baseline_value": comparison_info.get("baseline_roc_auc", 0.9888),
            "model_value": metrics["roc_auc"],
            "brier_score": metrics["brier_score"],
            "timestamp": metadata.training_timestamp,
        },
    ]
    pd.DataFrame(headline_rows).to_csv(headline_csv, index=False)

    print(f"\n==> Artifacts saved successfully:")
    print(f"    Model: {model_path}")
    print(f"    Metadata: {metadata_path}")
    print(f"    Comparison CSV: {comparison_csv}")
    print(f"    Headline CSV: {headline_csv}")
    return model


if __name__ == "__main__":
    train_gradient_boosting()
