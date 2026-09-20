"""
Canonical Data Contracts for NEXUS Explainability & Uncertainty (Phase 19).
Defines feature attributions, global/local explanations, calibration outputs,
uncertainty and out-of-distribution reports, and counterfactual sensitivity schemas.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from ml.risk_model.contracts import ModelMode, RiskFeatureRecord, RiskPredictionClass


class OutputSpace(str, Enum):
    LOG_ODDS = "LOG_ODDS"
    PROBABILITY_MARGIN = "PROBABILITY_MARGIN"
    DECISION_VALUE = "DECISION_VALUE"


class AttributionDirection(str, Enum):
    INCREASES_RISK = "INCREASES_RISK"
    DECREASES_RISK = "DECREASES_RISK"
    NEUTRAL = "NEUTRAL"


class DistributionStatus(str, Enum):
    IN_DISTRIBUTION = "IN_DISTRIBUTION"
    WARNING = "WARNING"
    OUT_OF_DISTRIBUTION = "OUT_OF_DISTRIBUTION"


class CalibrationMethod(str, Enum):
    PLATT_SCALING = "PLATT_SCALING"
    ISOTONIC = "ISOTONIC"
    UNAVAILABLE = "UNAVAILABLE"


class FeatureAttributionItem(BaseModel):
    """Specific attribution of a single feature to a model prediction."""
    feature_name: str = Field(..., description="Canonical feature key")
    display_name: str = Field(..., description="Human-readable label for operational displays")
    feature_value: float = Field(..., description="Observed raw feature value")
    unit: str = Field(..., description="Physical or statistical unit of measurement")
    standardized_value: float = Field(..., description="Zero-mean unit-variance transformed value")
    coefficient_or_weight: float = Field(..., description="Model weight or tree importance assigned to feature")
    contribution: float = Field(..., description="Numerical impact in output_space")
    direction: AttributionDirection = Field(..., description="Directional influence on predicted risk")
    explanation_text: str = Field(..., description="Non-causal descriptive explanation of contribution")


class LocalExplanation(BaseModel):
    """Local attribution report for an individual prediction."""
    prediction_id: str
    model_version: str
    feature_version: str = "v1.0"
    output_space: OutputSpace
    base_value: float = Field(..., description="Intercept or expected model output baseline")
    sum_contributions: float = Field(..., description="Sum of individual feature contributions")
    reconstructed_output: float = Field(..., description="base_value + sum_contributions")
    reconstruction_error: float = Field(default=0.0, description="Absolute difference between model output and reconstructed output")
    additive_reconstruction_passed: bool = Field(default=True, description="True if within numerical tolerance")
    attributions: List[FeatureAttributionItem] = Field(default_factory=list)


class GlobalFeatureSignal(BaseModel):
    """Population-level influence of a feature across training or evaluation splits."""
    feature_name: str
    display_name: str
    importance_or_weight: float
    rank: int
    unit: str
    description: str


class GlobalExplanation(BaseModel):
    """Global feature signal ranking for a model."""
    model_version: str
    algorithm: str
    dataset_fingerprint: str
    sample_size: int
    signals: List[GlobalFeatureSignal] = Field(default_factory=list)


class CalibrationResult(BaseModel):
    """Reliability and calibrated probability estimate."""
    raw_probability: float = Field(..., ge=0.0, le=1.0)
    calibrated_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    calibration_method: CalibrationMethod = CalibrationMethod.UNAVAILABLE
    calibration_version: str = "unavailable"
    brier_score_validation: Optional[float] = None
    expected_calibration_error_validation: Optional[float] = None
    is_calibrated: bool = False
    calibration_note: str = ""


class DataQualityReport(BaseModel):
    """Completeness and data hygiene assessment."""
    total_expected_features: int = 7
    available_features_count: int = 7
    missing_features: List[str] = Field(default_factory=list)
    imputed_features: List[str] = Field(default_factory=list)
    has_imputations: bool = False


class UncertaintyReport(BaseModel):
    """Multi-dimensional uncertainty assessment separating data quality from distribution shift."""
    data_quality: DataQualityReport
    distribution_status: DistributionStatus
    distance_from_centroid: float = Field(..., description="Standardized Euclidean distance from training distribution mean")
    distance_threshold_warning: float = 3.0
    distance_threshold_ood: float = 4.5
    uncertainty_notes: List[str] = Field(default_factory=list)


class CounterfactualFeatureDelta(BaseModel):
    """A required feature modification in a counterfactual scenario."""
    feature_name: str
    display_name: str
    current_value: float
    suggested_value: float
    delta: float
    unit: str


class CounterfactualSensitivity(BaseModel):
    """Sensitivity finding showing minimal perturbation required to shift risk class or margin."""
    counterfactual_id: str
    target_prediction_class: RiskPredictionClass
    current_probability: float
    target_probability: float
    probability_delta: float
    modified_features: List[CounterfactualFeatureDelta] = Field(default_factory=list)
    constraints_satisfied: bool = True
    method: str = "bounded_grid_sensitivity"
    limitations_note: str = "Statistically computed model sensitivity only. Does not imply real-world causal intervention."


class ComprehensiveRiskExplanation(BaseModel):
    """Authoritative combined prediction, explanation, calibration, and uncertainty payload."""
    prediction_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: ModelMode
    model_version: str
    feature_version: str = "v1.0"
    risk_probability: float = Field(..., ge=0.0, le=1.0)
    predicted_class: RiskPredictionClass
    local_explanation: LocalExplanation
    global_explanation_summary: List[GlobalFeatureSignal]
    calibration: CalibrationResult
    uncertainty: UncertaintyReport
    counterfactual: Optional[CounterfactualSensitivity] = None
    advisory_warning: str = (
        "NON-AUTONOMOUS ADVISORY NOTICE: Model predictions, attributions, and counterfactuals describe statistical "
        "correlations within model space and must NOT be interpreted as physical causality. Human DEOC authorization required."
    )
