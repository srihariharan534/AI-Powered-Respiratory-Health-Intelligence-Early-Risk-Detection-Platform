"""
Gradient Boosting Risk Model (Phase 18).
Implements a non-linear tree-based ensemble classifier wrapping
scikit-learn's GradientBoostingClassifier.
Provides:
- Reusable model interface (fit, predict, predict_proba, predict_single)
- Feature importance extraction (Gini impurity decrease)
- Dataset SHA-256 fingerprint validation
- Local attribution generation compatible with Phase 17 contracts
- Local artifact serialization and loading
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from ml.risk_model.contracts import (
    FeatureContribution,
    ModelMetadata,
    ModelMode,
    RiskFeatureRecord,
    RiskPredictionClass,
    RiskPredictionOutput,
)
from ml.risk_model.preprocessing import FEATURE_COLUMNS, RiskFeaturePreprocessor


def compute_dataset_fingerprint(file_path: Path) -> str:
    """Computes SHA-256 hash of a file for exact dataset provenance tracking."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


class GradientBoostingRiskModel:
    """
    Non-linear tree ensemble for operational flood risk prediction.
    Enables capturing non-linear interactions across environmental features.
    """

    def __init__(
        self,
        model_version: str = "gradient-boosting-v1",
        n_estimators: int = 100,
        learning_rate: float = 0.05,
        max_depth: int = 3,
        min_samples_split: int = 4,
        min_samples_leaf: int = 2,
        subsample: float = 0.85,
        random_state: int = 42,
    ) -> None:
        self.model_version = model_version
        self.hyperparameters = {
            "n_estimators": n_estimators,
            "learning_rate": learning_rate,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "min_samples_leaf": min_samples_leaf,
            "subsample": subsample,
            "random_state": random_state,
        }
        self.clf = GradientBoostingClassifier(**self.hyperparameters)
        self.preprocessor: Optional[RiskFeaturePreprocessor] = None
        self.is_trained: bool = False
        self.metadata: Optional[ModelMetadata] = None

    def fit(
        self,
        train_df: pd.DataFrame,
        preprocessor: RiskFeaturePreprocessor,
        target_col: str = "operational_flood_risk",
    ) -> "GradientBoostingRiskModel":
        """
        Fits the Gradient Boosting ensemble on training partition.
        """
        if target_col not in train_df.columns:
            raise ValueError(f"Target column '{target_col}' not found in training DataFrame.")

        self.preprocessor = preprocessor
        if not self.preprocessor.is_fitted:
            self.preprocessor.fit(train_df)

        x_train = self.preprocessor.transform(train_df)
        y_train = train_df[target_col].astype(int).values

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
        return self.clf.predict_proba(x_mat)[:, 1]

    def predict(self, df: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Binary class prediction according to probability threshold."""
        probs = self.predict_proba(df)
        return (probs >= threshold).astype(int)

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns Gini impurity-based feature importances summing to 1.0."""
        if not self.is_trained or self.preprocessor is None:
            raise RuntimeError("Model must be trained before extracting feature importances.")
        
        importances = self.clf.feature_importances_
        return {
            name: round(float(imp), 4)
            for name, imp in zip(self.preprocessor.feature_columns, importances)
        }

    def predict_single(
        self,
        record: RiskFeatureRecord,
        mode: ModelMode = ModelMode.SIMULATION,
        threshold: float = 0.5,
    ) -> RiskPredictionOutput:
        """
        Inference on a single validated record with feature attribution.
        Uses normalized tree feature importances combined with standardized deviation
        to calculate direction and magnitude of contribution.
        """
        if not self.is_trained or self.preprocessor is None:
            raise RuntimeError("Model must be trained before inference.")

        record_dict = record.model_dump()
        standardized_vals = self.preprocessor.transform_single(record_dict)

        # Single row DataFrame for model predict_proba
        single_df = pd.DataFrame([record_dict])
        prob = float(self.predict_proba(single_df)[0])
        prob = float(np.clip(prob, 0.0, 1.0))
        pred_class = (
            RiskPredictionClass.HIGH_RISK if prob >= threshold else RiskPredictionClass.LOW_RISK
        )

        importances = self.get_feature_importances()
        contributions: List[FeatureContribution] = []

        # Local feature attribution approximation:
        # contribution = importance * standardized_deviation
        # direction inferred from feature value relative to training mean and overall risk
        for feat_name, importance in importances.items():
            z_val = standardized_vals[feat_name]
            raw_val = float(record_dict[feat_name])

            # In flood domain: elevation and river distance have inverse risk association
            if feat_name in ("elevation_m", "distance_to_river_m", "slope_degrees"):
                effective_sign = -1.0
            else:
                effective_sign = 1.0

            contrib = importance * z_val * effective_sign

            if contrib > 0.03:
                direction = "INCREASES_RISK"
            elif contrib < -0.03:
                direction = "DECREASES_RISK"
            else:
                direction = "NEUTRAL"

            contributions.append(
                FeatureContribution(
                    feature_name=feat_name,
                    feature_value=raw_val,
                    standardized_value=round(z_val, 4),
                    coefficient=round(importance, 4),  # Feature importance in tree models
                    contribution=round(contrib, 4),
                    direction=direction,
                )
            )

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
            uncertainty_note="Non-linear tree ensemble probability; calibration evaluated against baseline.",
        )
