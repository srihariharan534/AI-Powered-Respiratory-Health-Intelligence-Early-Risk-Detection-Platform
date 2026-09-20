"""
Uncertainty and data quality diagnostics for NEXUS risk models.
Distinguishes between:
1. Input Data Quality (missing features, imputed fields)
2. Distribution Shift / Distance from Training Centroid (OOD checks)
3. Model Extrapolation Warnings
"""

from typing import Any, Dict, List, Optional
import numpy as np

from ml.explainability.contracts import (
    DataQualityReport,
    DistributionStatus,
    UncertaintyReport,
)
from ml.explainability.uncertainty.bounds import (
    DISTANCE_THRESHOLD_OOD,
    DISTANCE_THRESHOLD_WARNING,
    PHYSICAL_FEATURE_BOUNDS,
)
from ml.risk_model.contracts import RiskFeatureRecord
from ml.risk_model.preprocessing import RiskFeaturePreprocessor


class UncertaintyDiagnostics:
    """
    Evaluates data quality and distribution shift without fabricating statistical certainty.
    """

    def __init__(
        self,
        preprocessor: RiskFeaturePreprocessor,
        dist_warn: float = DISTANCE_THRESHOLD_WARNING,
        dist_ood: float = DISTANCE_THRESHOLD_OOD,
    ) -> None:
        self.preprocessor = preprocessor
        self.dist_warn = dist_warn
        self.dist_ood = dist_ood

    def evaluate_uncertainty(
        self,
        record: RiskFeatureRecord,
        raw_input_dict: Optional[Dict[str, Any]] = None,
    ) -> UncertaintyReport:
        """
        Assesses data quality and distribution distance for a single observation.
        """
        record_dict = record.model_dump()
        raw_dict = raw_input_dict or record_dict

        missing: List[str] = []
        imputed: List[str] = []
        notes: List[str] = []

        # 1. Data Quality Assessment
        for col in self.preprocessor.feature_columns:
            val = raw_dict.get(col)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                missing.append(col)
                imputed.append(col)
                notes.append(
                    f"Feature '{col}' was missing in input; imputed with training median {self.preprocessor.medians_[col]}."
                )

        data_quality = DataQualityReport(
            total_expected_features=len(self.preprocessor.feature_columns),
            available_features_count=len(self.preprocessor.feature_columns) - len(missing),
            missing_features=missing,
            imputed_features=imputed,
            has_imputations=len(imputed) > 0,
        )

        # 2. Standardized Centroid Distance (Mahalanobis under diagonal assumption)
        standardized_vals = self.preprocessor.transform_single(record_dict)
        sum_sq = sum(standardized_vals[col] ** 2 for col in self.preprocessor.feature_columns)
        distance = float(np.sqrt(sum_sq))

        # 3. Distribution Classification
        if distance > self.dist_ood:
            status = DistributionStatus.OUT_OF_DISTRIBUTION
            notes.append(
                f"Extreme anomaly detected: standardized distance {distance:.2f} exceeds OOD threshold {self.dist_ood:.2f}."
            )
        elif distance > self.dist_warn:
            status = DistributionStatus.WARNING
            notes.append(
                f"Unusual feature combination: standardized distance {distance:.2f} exceeds warning threshold {self.dist_warn:.2f}."
            )
        else:
            status = DistributionStatus.IN_DISTRIBUTION

        # 4. Extreme single feature checks
        for col in self.preprocessor.feature_columns:
            z = abs(standardized_vals[col])
            if z > 4.0:
                notes.append(f"Tail value for '{col}': {record_dict[col]} is {z:.1f} standard deviations from mean.")

        if not notes:
            notes.append("Observation falls well within typical training distribution envelope; all features complete.")

        return UncertaintyReport(
            data_quality=data_quality,
            distribution_status=status,
            distance_from_centroid=round(distance, 4),
            distance_threshold_warning=self.dist_warn,
            distance_threshold_ood=self.dist_ood,
            uncertainty_notes=notes,
        )
