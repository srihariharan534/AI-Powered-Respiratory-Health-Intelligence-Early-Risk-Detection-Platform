"""
Standalone Evaluation Script for Baseline Flood Risk Model (Phase 17).
Usage:
    python scripts/evaluate/evaluate_baseline_risk.py [--data PATH] [--model PATH]

Evaluates a serialized risk model artifact against a test dataset without retraining.
Outputs comprehensive classification, probability calibration, and confusion matrix metrics.
"""

import argparse
import json
import sys
from pathlib import Path
import joblib
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.risk_model.baseline.logistic_regression.evaluation import (
    evaluate_majority_class_baseline,
    evaluate_risk_predictions,
)
from ml.risk_model.preprocessing import FEATURE_COLUMNS


def run_evaluation(model_path: Path, data_path: Path) -> dict:
    print(f"==> Loading model artifact from: {model_path}")
    if not model_path.is_file():
        raise FileNotFoundError(f"Model artifact not found: {model_path}")
    model = joblib.load(model_path)

    print(f"==> Loading dataset from: {data_path}")
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {data_path}")
    df = pd.read_csv(data_path)

    # Use test partition if full dataset is provided
    if "operational_flood_risk" not in df.columns:
        raise ValueError("Dataset missing ground-truth label 'operational_flood_risk'.")

    # If full dataset, take test split (last 15%)
    if len(df) >= 100:
        test_df = df.iloc[int(len(df) * 0.85) :].copy()
    else:
        test_df = df.copy()

    print(f"    Evaluating on {len(test_df)} observations...")
    y_true = test_df["operational_flood_risk"].values
    y_prob = model.predict_proba(test_df)

    metrics = evaluate_risk_predictions(y_true, y_prob)
    baseline = evaluate_majority_class_baseline(y_true)

    print("\n--- EVALUATION SUMMARY ---")
    print(f"Model Version: {model.model_version}")
    print(f"Test Samples: {metrics['sample_count']} (Positive rate: {metrics['positive_rate']:.2%})")
    print(f"Accuracy:      {metrics['accuracy']:.4f} (Baseline: {baseline['accuracy']:.4f})")
    print(f"Precision:     {metrics['precision']:.4f}")
    print(f"Recall:        {metrics['recall']:.4f}")
    print(f"F1 Score:      {metrics['f1_score']:.4f}")
    print(f"ROC-AUC:       {metrics['roc_auc']:.4f} (Baseline: 0.5000)")
    print(f"PR-AUC:        {metrics['pr_auc']:.4f}")
    print(f"Brier Score:   {metrics['brier_score']:.4f} (Baseline: {baseline['brier_score']:.4f})")
    print(f"Expected Cal Error: {metrics['expected_calibration_error']:.4f}")
    print(f"Confusion Matrix: {metrics['confusion_matrix']}")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate NEXUS Baseline Risk Model")
    parser.add_argument(
        "--model",
        type=Path,
        default=ROOT_DIR / "ml" / "risk_model" / "artifacts" / "baseline_logistic_regression_v1.joblib",
        help="Path to serialized .joblib model",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=ROOT_DIR / "ml" / "risk_model" / "data" / "reference_flood_risk_dataset.csv",
        help="Path to evaluation CSV dataset",
    )
    args = parser.parse_args()
    run_evaluation(args.model, args.data)
