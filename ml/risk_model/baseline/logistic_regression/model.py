"""
Baseline Logistic Regression Model for Operational Flood Risk (Phase 17).
Provides reproducible training, prediction, standardized coefficient interpretation,
and local linear feature attribution.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from ml.risk_model.contracts import (
    FeatureContribution,
    ModelMetadata,
    ModelMode,
    RiskFeatureRecord,
    RiskPredictionClass,
    RiskPredictionOutput,
)
from ml.risk_model.preprocessing import RiskFeaturePreprocessor


class BaselineLogisticRegressionModel:
    """
    Interpretable baseline risk model wrapping scikit-learn's LogisticRegression.
    Features are standardized prior to fitting, meaning coefficients directly reflect
    the change in log-odds of operational flood risk per standard deviation of each feature.
    """

    def __init__(
        self,
        model_version: str = "baseline-logistic-regression-v1",
        penalty: str = "l2",
        c_param: float = 1.0,
        random_state: int = 42,
    ) -> None:
        self.model_version = model_version
        self.penalty = penalty
        self.c_param = c_param
        self.random_state = random_state
        self.clf = LogisticRegression(
            C=self.c_param,
            solver="lbfgs",
            random_state=self.random_state,
            max_iter=1000,
        )
        self.preprocessor: Optional[RiskFeaturePreprocessor] = None
        self.is_trained: bool = False
        self.metadata: Optional[ModelMetadata] = None

    def fit(
        self,
        train_df: pd.DataFrame,
        preprocessor: RiskFeaturePreprocessor,
        target_col: str = "operational_flood_risk",
    ) -> "BaselineLogisticRegressionModel":
        """
        Fits the preprocessor and Logistic Regression classifier on training data.
        """
        if target_col not in train_df.columns:
            raise ValueError(f"Target column '{target_col}' not found in training DataFrame.")

        self.preprocessor = preprocessor
        if not self.preprocessor.is_fitted:
            self.preprocessor.fit(train_df)

        x_train = self.preprocessor.transform(train_df)
        y_train = train_df[target_col].astype(int).values

        # Ensure both classes exist in training
        classes = np.unique(y_train)
        if len(classes) < 2:
            raise ValueError(f"Training data must contain at least 2 distinct classes, found {classes}")

        self.clf.fit(x_train, y_train)
        self.is_trained = True
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """Estimate P(operational_flood_risk = 1 | X)."""
        if not self.is_trained or self.preprocessor is None:
            raise RuntimeError("Model must be trained before predicting.")
        x_mat = self.preprocessor.transform(df)
        # Class 1 probability is second column
        return self.clf.predict_proba(x_mat)[:, 1]

    def predict(self, df: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Class prediction according to classification probability threshold."""
        probs = self.predict_proba(df)
        return (probs >= threshold).astype(int)

    def get_coefficients(self) -> Dict[str, float]:
        """Return named standardized logistic regression coefficients."""
        if not self.is_trained or self.preprocessor is None:
            raise RuntimeError("Model must be trained before extracting coefficients.")
        
        coef_dict = {}
        weights = self.clf.coef_[0]
        for name, weight in zip(self.preprocessor.feature_columns, weights):
            coef_dict[name] = float(weight)
        return coef_dict

    def get_intercept(self) -> float:
        """Return model intercept (log-odds when all features are at their mean)."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before extracting intercept.")
        return float(self.clf.intercept_[0])

    def predict_single(
        self,
        record: RiskFeatureRecord,
        mode: ModelMode = ModelMode.SIMULATION,
        threshold: float = 0.5,
    ) -> RiskPredictionOutput:
        """
        Perform inference on a single validated feature record and provide
        deterministic local linear feature attributions.
        """
        if not self.is_trained or self.preprocessor is None:
            raise RuntimeError("Model must be trained before inference.")

        record_dict = record.model_dump()
        standardized_vals = self.preprocessor.transform_single(record_dict)
        
        # Calculate log-odds: intercept + sum(w_i * z_i)
        intercept = self.get_intercept()
        coefficients = self.get_coefficients()
        
        contributions: List[FeatureContribution] = []
        log_odds = intercept

        for feat_name, coef in coefficients.items():
            z_val = standardized_vals[feat_name]
            raw_val = float(record_dict[feat_name])
            contrib = coef * z_val
            log_odds += contrib

            if contrib > 0.05:
                direction = "INCREASES_RISK"
            elif contrib < -0.05:
                direction = "DECREASES_RISK"
            else:
                direction = "NEUTRAL"

            contributions.append(
                FeatureContribution(
                    feature_name=feat_name,
                    feature_value=raw_val,
                    standardized_value=round(z_val, 4),
                    coefficient=round(coef, 4),
                    contribution=round(contrib, 4),
                    direction=direction,
                )
            )

        # Sigmoid probability
        prob = 1.0 / (1.0 + np.exp(-log_odds))
        prob = float(np.clip(prob, 0.0, 1.0))
        pred_class = (
            RiskPredictionClass.HIGH_RISK if prob >= threshold else RiskPredictionClass.LOW_RISK
        )

        # Sort contributions by absolute impact descending
        contributions.sort(key=lambda c: abs(c.contribution), reverse=True)

        return RiskPredictionOutput(
            sample_id=record.sample_id,
            risk_probability=round(prob, 4),
            predicted_class=pred_class,
            model_version=self.model_version,
            feature_version="v1.0",
            timestamp=datetime.now(timezone.utc),
            mode=mode,
            feature_contributions=contributions,
            uncertainty_note="Linear logistic probability; calibration measured in evaluation reports.",
        )
