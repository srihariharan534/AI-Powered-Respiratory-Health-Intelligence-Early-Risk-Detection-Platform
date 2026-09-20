"""
Evaluation Metrics, Probability Quality, and Calibration Analysis for Risk Models.
Computes ROC-AUC, PR-AUC, Brier score, calibration curve, confusion matrix,
and comparative metrics against naive baselines.
"""

from typing import Any, Dict
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
)
from sklearn.calibration import calibration_curve


def evaluate_risk_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Evaluates binary classification and probabilistic predictions.
    Returns standard metrics, confusion matrix, probability quality metrics,
    and calibration points.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    # Classification metrics
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    # Area under curves (requires both classes to be present)
    if len(np.unique(y_true)) > 1:
        roc_auc = float(roc_auc_score(y_true, y_prob))
        pr_auc = float(average_precision_score(y_true, y_prob))
    else:
        roc_auc = 0.5
        pr_auc = float(np.mean(y_true))

    # Probability quality metrics
    brier = float(brier_score_loss(y_true, y_prob))

    # Calibration curve (reliability)
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=5, strategy="uniform")
    calibration_data = [
        {"bin_predicted": round(float(p_pred), 4), "bin_actual": round(float(p_true), 4)}
        for p_pred, p_true in zip(prob_pred, prob_true)
    ]

    # Expected Calibration Error (ECE) approximation
    ece = float(np.mean(np.abs(prob_true - prob_pred))) if len(prob_true) > 0 else 0.0

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "expected_calibration_error": round(ece, 4),
        "confusion_matrix": {
            "true_positive": int(tp),
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
        },
        "calibration_curve": calibration_data,
        "sample_count": len(y_true),
        "positive_rate": round(float(np.mean(y_true)), 4),
    }


def evaluate_majority_class_baseline(y_true: np.ndarray) -> Dict[str, Any]:
    """
    Computes baseline metrics for a trivial majority-class classifier
    to verify that the machine learning model demonstrates genuine predictive signal.
    """
    y_true = np.asarray(y_true, dtype=int)
    pos_rate = float(np.mean(y_true))
    majority_class = 1 if pos_rate >= 0.5 else 0

    # Constant prediction
    y_prob = np.full_like(y_true, fill_value=pos_rate, dtype=float)
    y_pred = np.full_like(y_true, fill_value=majority_class, dtype=int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    brier = float(brier_score_loss(y_true, y_prob))

    return {
        "baseline_type": "majority_class",
        "predicted_constant_class": majority_class,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": 0.5,
        "pr_auc": round(pos_rate, 4),
        "brier_score": round(brier, 4),
        "confusion_matrix": {
            "true_positive": int(tp),
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
        },
    }
