"""
Deterministic Training Script for Baseline Flood Risk Model (Phase 17).
Usage:
    python scripts/train/train_baseline_risk.py

Operations:
1. Loads documented reference dataset.
2. Validates schema and value boundaries.
3. Splits into Train (70%), Validation (15%), and Test (15%) splits without data leakage.
4. Fits RiskFeaturePreprocessor on Train split.
5. Fits BaselineLogisticRegressionModel.
6. Evaluates model against Test split (ROC-AUC, PR-AUC, Brier score, calibration, confusion matrix).
7. Evaluates majority-class naive baseline for direct comparative benchmark.
8. Saves model artifact (.joblib) and metadata JSON to ml/risk_model/artifacts/.
9. Writes comparative metrics table to evaluation/results/tables/model_comparison.csv and headline_metrics.csv.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import joblib
import numpy as np
import pandas as pd

from ml.risk_model.baseline.logistic_regression.evaluation import (
    evaluate_majority_class_baseline,
    evaluate_risk_predictions,
)
from ml.risk_model.baseline.logistic_regression.model import (
    BaselineLogisticRegressionModel,
)
from ml.risk_model.contracts import ModelMetadata
from ml.risk_model.preprocessing import FEATURE_COLUMNS, RiskFeaturePreprocessor

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = ROOT_DIR / "ml" / "risk_model" / "data" / "reference_flood_risk_dataset.csv"
ARTIFACTS_DIR = ROOT_DIR / "ml" / "risk_model" / "artifacts"
RESULTS_DIR = ROOT_DIR / "evaluation" / "results" / "tables"


def train_baseline(
    data_path: Path = DATA_PATH,
    artifacts_dir: Path = ARTIFACTS_DIR,
    results_dir: Path = RESULTS_DIR,
    random_seed: int = 42,
) -> BaselineLogisticRegressionModel:
    """Trains the baseline logistic regression risk model."""
    print(f"==> Loading reference risk dataset from: {data_path}")
    if not data_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. Run ml/risk_model/data/generator.py first."
        )

    df = pd.read_csv(data_path)
    print(f"    Loaded {len(df)} records. Columns: {list(df.columns)}")
    
    # 1. Validate required columns
    required = FEATURE_COLUMNS + ["operational_flood_risk", "dataset_mode"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing from dataset.")

    # 2. Split into Train (70%), Validation (15%), Test (15%) deterministically
    # Sort deterministically by timestamp and sample_id to prevent random shuffle leakage
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

    # 4. Fit Baseline Logistic Regression Model
    model = BaselineLogisticRegressionModel(
        model_version="baseline-logistic-regression-v1",
        penalty="l2",
        c_param=1.0,
        random_state=random_seed,
    )
    model.fit(train_df, preprocessor, target_col="operational_flood_risk")

    # 5. Evaluate on Test split
    y_test = test_df["operational_flood_risk"].values
    y_prob = model.predict_proba(test_df)
    metrics = evaluate_risk_predictions(y_test, y_prob)

    # 6. Evaluate Naive Majority Baseline
    baseline_metrics = evaluate_majority_class_baseline(y_test)

    print("\n==> Evaluation Metrics on Test Partition:")
    print(f"    Accuracy: {metrics['accuracy']:.4f} (Baseline: {baseline_metrics['accuracy']:.4f})")
    print(f"    Precision: {metrics['precision']:.4f}")
    print(f"    Recall: {metrics['recall']:.4f}")
    print(f"    F1 Score: {metrics['f1_score']:.4f}")
    print(f"    ROC-AUC: {metrics['roc_auc']:.4f} (Baseline: 0.5000)")
    print(f"    PR-AUC: {metrics['pr_auc']:.4f} (Baseline: {baseline_metrics['pr_auc']:.4f})")
    print(f"    Brier Score: {metrics['brier_score']:.4f} (Lower is better; Baseline: {baseline_metrics['brier_score']:.4f})")
    print(f"    Expected Calibration Error (ECE): {metrics['expected_calibration_error']:.4f}")

    print("\n==> Standardized Coefficients (Log-Odds Impact):")
    coefficients = model.get_coefficients()
    for feat, coef in sorted(coefficients.items(), key=lambda x: abs(x[1]), reverse=True):
        direction = "[+] INCREASES RISK" if coef > 0 else "[-] DECREASES RISK"
        print(f"    {feat:30s}: {coef:+.4f} ({direction})")

    # 7. Create Model Metadata
    metadata = ModelMetadata(
        model_id="NEXUS-RISK-BASELINE-001",
        model_version=model.model_version,
        algorithm="Logistic Regression (L2 Regularized, C=1.0, Standardized Features)",
        target_definition="Binary operational disruption/inundation >= 15cm (0=nominal, 1=risk)",
        training_dataset_id="reference_flood_risk_dataset_v1",
        dataset_mode="SYNTHETIC_SCENARIO_OBSERVATION",
        feature_names=FEATURE_COLUMNS,
        coefficients=coefficients,
        intercept=model.get_intercept(),
        metrics=metrics,
        comparison_to_baseline=baseline_metrics,
        training_timestamp=datetime.now(timezone.utc).isoformat(),
        random_seed=random_seed,
        limitations=[
            "Linear decision boundary; cannot capture complex non-linear hydrodynamic interactions.",
            "Standardized feature coefficients assume additive effects in log-odds.",
            "Dataset is based on scenario observations; real-world field validation required before operational deployment.",
            "Model uncertainty is not formally estimated; raw logistic probabilities reported.",
            "Does NOT decide evacuation priority or autonomous road/hospital closures.",
        ],
    )
    model.metadata = metadata

    # 8. Save Artifacts
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifacts_dir / "baseline_logistic_regression_v1.joblib"
    joblib.dump(model, model_path)

    metadata_path = artifacts_dir / "baseline_logistic_regression_v1_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=2)

    # 9. Write comparative CSV tables for Phase 18 and evaluation benchmarks
    comparison_row = {
        "model_version": model.model_version,
        "algorithm": "Logistic Regression (Baseline)",
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

    majority_row = {
        "model_version": "naive-majority-class",
        "algorithm": "Majority Class Classifier (Baseline)",
        "test_samples": metrics["sample_count"],
        "accuracy": baseline_metrics["accuracy"],
        "precision": baseline_metrics["precision"],
        "recall": baseline_metrics["recall"],
        "f1_score": baseline_metrics["f1_score"],
        "roc_auc": 0.5000,
        "pr_auc": baseline_metrics["pr_auc"],
        "brier_score": baseline_metrics["brier_score"],
        "ece": 0.0,
        "dataset_mode": metadata.dataset_mode,
        "timestamp": metadata.training_timestamp,
    }

    comparison_df = pd.DataFrame([majority_row, comparison_row])
    comparison_csv = results_dir / "model_comparison.csv"
    comparison_df.to_csv(comparison_csv, index=False)

    headline_df = pd.DataFrame([{
        "benchmark": "Phase 17 Risk Model Baseline",
        "primary_metric": "roc_auc",
        "baseline_value": 0.5000,
        "model_value": metrics["roc_auc"],
        "brier_score": metrics["brier_score"],
        "timestamp": metadata.training_timestamp,
    }])
    headline_csv = results_dir / "headline_metrics.csv"
    headline_df.to_csv(headline_csv, index=False)

    print(f"\n==> Artifacts saved:")
    print(f"    Model: {model_path}")
    print(f"    Metadata: {metadata_path}")
    print(f"    Comparison CSV: {comparison_csv}")
    print(f"    Headline CSV: {headline_csv}")
    return model


if __name__ == "__main__":
    train_baseline()
