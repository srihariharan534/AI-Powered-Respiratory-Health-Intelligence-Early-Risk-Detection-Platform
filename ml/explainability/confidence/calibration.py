"""
Confidence and probability calibration layer for NEXUS operational flood risk models.
Ensures probabilities are empirically grounded, measuring reliability via Brier score and ECE,
and fitting calibration transformations strictly on validation partitions to prevent test leakage.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

from ml.explainability.contracts import CalibrationMethod, CalibrationResult
from ml.risk_model.preprocessing import RiskFeaturePreprocessor


class RiskProbabilityCalibrator:
    """
    Fits and manages probability calibration (Platt scaling / Sigmoid or Isotonic)
    strictly on validation splits.
    """

    def __init__(
        self,
        base_model: Any,
        preprocessor: RiskFeaturePreprocessor,
        method: CalibrationMethod = CalibrationMethod.PLATT_SCALING,
        calibration_version: str = "calib-v1.0",
    ) -> None:
        self.base_model = base_model
        self.preprocessor = preprocessor
        self.method = method
        self.calibration_version = calibration_version
        self.calibrator_model: Any = None
        self.is_fitted: bool = False
        self.validation_brier: Optional[float] = None
        self.validation_ece: Optional[float] = None
        self.raw_validation_brier: Optional[float] = None

    def fit_on_validation(
        self,
        val_df: pd.DataFrame,
        target_col: str = "operational_flood_risk",
    ) -> "RiskProbabilityCalibrator":
        """
        Fits calibration transformation strictly on validation split probabilities.
        Never touches the final test split.
        """
        if target_col not in val_df.columns:
            raise ValueError(f"Target column '{target_col}' missing from validation data.")

        y_val = val_df[target_col].astype(int).values
        raw_probs = self.base_model.predict_proba(val_df)
        self.raw_validation_brier = float(brier_score_loss(y_val, raw_probs))

        # Shape raw probabilities into (N, 1) matrix
        x_prob = raw_probs.reshape(-1, 1)

        if self.method == CalibrationMethod.PLATT_SCALING:
            # Platt scaling fits a 1D logistic regression over the raw predictions
            self.calibrator_model = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
            self.calibrator_model.fit(x_prob, y_val)
            cal_probs = self.calibrator_model.predict_proba(x_prob)[:, 1]
        else:
            # Isotonic regression
            self.calibrator_model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            self.calibrator_model.fit(raw_probs, y_val)
            cal_probs = self.calibrator_model.predict(raw_probs)

        self.is_fitted = True
        self.validation_brier = float(brier_score_loss(y_val, cal_probs))

        prob_true, prob_pred = calibration_curve(y_val, cal_probs, n_bins=5, strategy="uniform")
        self.validation_ece = float(np.mean(np.abs(prob_true - prob_pred))) if len(prob_true) > 0 else 0.0

        return self

    def calibrate_probability(self, raw_prob: float, record_dict: Dict[str, Any]) -> CalibrationResult:
        """
        Returns calibrated probability alongside validation benchmark metrics.
        """
        if not self.is_fitted or self.calibrator_model is None:
            return CalibrationResult(
                raw_probability=round(raw_prob, 4),
                calibrated_probability=None,
                calibration_method=CalibrationMethod.UNAVAILABLE,
                calibration_version="unavailable",
                is_calibrated=False,
                calibration_note="Calibration model not fitted; using raw probability.",
            )

        # Single observation calibration
        if self.method == CalibrationMethod.PLATT_SCALING:
            x_single = np.array([[raw_prob]])
            cal_prob = float(self.calibrator_model.predict_proba(x_single)[0, 1])
        else:
            cal_prob = float(self.calibrator_model.predict([raw_prob])[0])

        cal_prob = float(np.clip(cal_prob, 0.0, 1.0))
        note = (
            f"Calibrated via {self.method.value} on validation split. "
            f"Validation Brier score: {self.validation_brier:.4f} vs raw {self.raw_validation_brier:.4f}."
        )

        return CalibrationResult(
            raw_probability=round(raw_prob, 4),
            calibrated_probability=round(cal_prob, 4),
            calibration_method=self.method,
            calibration_version=self.calibration_version,
            brier_score_validation=round(self.validation_brier, 4) if self.validation_brier else None,
            expected_calibration_error_validation=round(self.validation_ece, 4) if self.validation_ece else None,
            is_calibrated=True,
            calibration_note=note,
        )

