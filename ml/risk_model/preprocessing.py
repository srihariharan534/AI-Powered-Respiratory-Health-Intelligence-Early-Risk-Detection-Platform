"""
Feature Preprocessing and Transformation Pipeline for NEXUS Risk Models.
Ensures deterministic missing value imputation and numerical standardization
fitted strictly on training splits.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "rainfall_mm_1h",
    "rainfall_mm_24h",
    "elevation_m",
    "distance_to_river_m",
    "slope_degrees",
    "road_density_km",
    "infrastructure_exposure_count",
]


class RiskFeaturePreprocessor:
    """
    Deterministic feature preprocessor for tabular flood risk features.
    Computes and persists median imputations and standard scaler parameters (mean, std).
    """

    def __init__(self, feature_columns: Optional[List[str]] = None) -> None:
        self.feature_columns = feature_columns or list(FEATURE_COLUMNS)
        self.means_: Dict[str, float] = {}
        self.stds_: Dict[str, float] = {}
        self.medians_: Dict[str, float] = {}
        self.is_fitted: bool = False

    def fit(self, df: pd.DataFrame) -> "RiskFeaturePreprocessor":
        """
        Fit preprocessor strictly on the training partition.
        Calculates medians for missing data imputation and means/stds for standardization.
        """
        for col in self.feature_columns:
            if col not in df.columns:
                raise ValueError(f"Required feature column '{col}' missing from training DataFrame.")
            
            series = df[col].dropna()
            if len(series) == 0:
                raise ValueError(f"Feature column '{col}' contains only null values.")

            med = float(series.median())
            mean = float(series.mean())
            std = float(series.std(ddof=0))
            if std == 0.0 or np.isnan(std):
                std = 1.0  # Avoid division by zero for constant features

            self.medians_[col] = med
            self.means_[col] = mean
            self.stds_[col] = std

        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        Transform a DataFrame into standardized feature matrix X.
        Applies median imputation if nulls exist, then applies standard scaling:
        z = (x - mean) / std.
        """
        if not self.is_fitted:
            raise RuntimeError("RiskFeaturePreprocessor must be fitted before transform.")

        transformed_cols = []
        for col in self.feature_columns:
            if col not in df.columns:
                raise ValueError(f"Feature column '{col}' missing from input DataFrame.")
            
            # Fill missing with fitted training median
            val = df[col].fillna(self.medians_[col]).astype(float)
            scaled = (val - self.means_[col]) / self.stds_[col]
            transformed_cols.append(scaled.values)

        return np.column_stack(transformed_cols)

    def transform_single(self, record_dict: Dict[str, Any]) -> Dict[str, float]:
        """
        Transform a single record returning both raw and standardized values per feature.
        """
        if not self.is_fitted:
            raise RuntimeError("RiskFeaturePreprocessor must be fitted before transform.")

        standardized: Dict[str, float] = {}
        for col in self.feature_columns:
            raw_val = record_dict.get(col)
            if raw_val is None or (isinstance(raw_val, float) and np.isnan(raw_val)):
                raw_val = self.medians_[col]
            else:
                raw_val = float(raw_val)
            standardized[col] = (raw_val - self.means_[col]) / self.stds_[col]

        return standardized

    def to_dict(self) -> Dict[str, Any]:
        """Serialize preprocessor configuration for artifact storage."""
        return {
            "feature_columns": self.feature_columns,
            "means": self.means_,
            "stds": self.stds_,
            "medians": self.medians_,
            "is_fitted": self.is_fitted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskFeaturePreprocessor":
        """Deserialize preprocessor from metadata dictionary."""
        instance = cls(feature_columns=data["feature_columns"])
        instance.means_ = data["means"]
        instance.stds_ = data["stds"]
        instance.medians_ = data["medians"]
        instance.is_fitted = data["is_fitted"]
        return instance
