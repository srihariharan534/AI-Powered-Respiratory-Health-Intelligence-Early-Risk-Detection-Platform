"""
NEXUS Baseline Risk Model Package (Phase 17).
Exports contracts, preprocessing, models, and evaluation routines.
"""

from ml.risk_model.baseline.logistic_regression.evaluation import (
    evaluate_majority_class_baseline,
    evaluate_risk_predictions,
)
from ml.risk_model.baseline.logistic_regression.model import (
    BaselineLogisticRegressionModel,
)
from ml.risk_model.gradient_boosting.model import (
    GradientBoostingRiskModel,
    compute_dataset_fingerprint,
)
from ml.risk_model.contracts import (
    FeatureContribution,
    ModelMetadata,
    ModelMode,
    RiskFeatureRecord,
    RiskPredictionClass,
    RiskPredictionOutput,
)
from ml.risk_model.preprocessing import (
    FEATURE_COLUMNS,
    RiskFeaturePreprocessor,
)

__all__ = [
    "BaselineLogisticRegressionModel",
    "GradientBoostingRiskModel",
    "compute_dataset_fingerprint",
    "RiskFeaturePreprocessor",
    "FEATURE_COLUMNS",
    "RiskFeatureRecord",
    "RiskPredictionOutput",
    "RiskPredictionClass",
    "ModelMode",
    "FeatureContribution",
    "ModelMetadata",
    "evaluate_risk_predictions",
    "evaluate_majority_class_baseline",
]
