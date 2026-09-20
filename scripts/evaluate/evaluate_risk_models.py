"""
Unified Comparative Evaluation Script for NEXUS Risk Models (Phase 18).
Usage:
    python scripts/evaluate/evaluate_risk_models.py [--data PATH]

Loads all trained model artifacts (Logistic Regression Baseline & Gradient Boosting),
evaluates both against the identical test partition under equal conditions,
and prints a side-by-side comparative table with latency measurements.
"""

import argparse
import sys
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.risk_model.baseline.logistic_regression.evaluation import (
    evaluate_majority_class_baseline,
    evaluate_risk_predictions,
)

ARTIFACTS_DIR = ROOT_DIR / "ml" / "risk_model" / "artifacts"
DATA_PATH = ROOT_DIR / "ml" / "risk_model" / "data" / "reference_flood_risk_dataset.csv"


def compare_models(data_path: Path = DATA_PATH, artifacts_dir: Path = ARTIFACTS_DIR) -> pd.DataFrame:
    print(f"==> Evaluating models against dataset: {data_path}")
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    if "operational_flood_risk" not in df.columns:
        raise ValueError("Dataset missing 'operational_flood_risk' target.")

    # Sort and take test split (last 15%)
    df = df.sort_values(by=["timestamp", "sample_id"]).reset_index(drop=True)
    test_df = df.iloc[int(len(df) * 0.85) :].copy()
    y_test = test_df["operational_flood_risk"].values
    n_test = len(test_df)
    pos_rate = float(np.mean(y_test))

    print(f"    Test partition: {n_test} samples (Positive rate: {pos_rate:.1%})\n")

    # 1. Naive Majority Baseline
    majority = evaluate_majority_class_baseline(y_test)
    rows = [
        {
            "Model Version": "naive-majority-class",
            "Algorithm": "Majority Class Classifier",
            "Accuracy": f"{majority['accuracy']:.4f}",
            "Precision": f"{majority['precision']:.4f}",
            "Recall": f"{majority['recall']:.4f}",
            "F1-Score": f"{majority['f1_score']:.4f}",
            "ROC-AUC": "0.5000",
            "PR-AUC": f"{majority['pr_auc']:.4f}",
            "Brier Score": f"{majority['brier_score']:.4f}",
            "ECE": "0.0000",
            "Mean Latency": "0.00 ms",
        }
    ]

    # Models to inspect
    model_files = [
        ("baseline-logistic-regression-v1", artifacts_dir / "baseline_logistic_regression_v1.joblib"),
        ("gradient-boosting-v1", artifacts_dir / "gradient_boosting_v1.joblib"),
    ]

    for version, model_path in model_files:
        if not model_path.is_file():
            print(f"[!] Warning: Model artifact '{version}' not found at {model_path}. Skipping.")
            continue

        model = joblib.load(model_path)
        t0 = time.perf_counter()
        y_prob = model.predict_proba(test_df)
        total_time_ms = (time.perf_counter() - t0) * 1000.0
        mean_latency_ms = total_time_ms / n_test

        metrics = evaluate_risk_predictions(y_test, y_prob)

        rows.append(
            {
                "Model Version": model.model_version,
                "Algorithm": type(model).__name__,
                "Accuracy": f"{metrics['accuracy']:.4f}",
                "Precision": f"{metrics['precision']:.4f}",
                "Recall": f"{metrics['recall']:.4f}",
                "F1-Score": f"{metrics['f1_score']:.4f}",
                "ROC-AUC": f"{metrics['roc_auc']:.4f}",
                "PR-AUC": f"{metrics['pr_auc']:.4f}",
                "Brier Score": f"{metrics['brier_score']:.4f}",
                "ECE": f"{metrics['expected_calibration_error']:.4f}",
                "Mean Latency": f"{mean_latency_ms:.3f} ms",
            }
        )

    summary_df = pd.DataFrame(rows)
    print("========================= COMPARATIVE EVALUATION SUMMARY =========================")
    print(summary_df.to_string(index=False))
    print("==================================================================================\n")
    return summary_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare NEXUS Risk Models")
    parser.add_argument("--data", type=Path, default=DATA_PATH, help="Path to evaluation dataset")
    args = parser.parse_args()
    compare_models(data_path=args.data)
