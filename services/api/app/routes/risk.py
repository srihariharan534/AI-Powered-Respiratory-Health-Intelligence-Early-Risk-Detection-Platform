"""
Operational Flood Risk REST API Endpoints (Phase 17).
Provides:
- POST /api/v1/risk/predict: Single point inference with linear feature attributions
- POST /api/v1/risk/batch: Batch point predictions
- GET /api/v1/risk/model-info: Model metadata, coefficients, and calibration summaries
- POST /api/v1/risk/geojson: GeoJSON FeatureCollection export for map visualization
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ml.explainability.contracts import (
    CalibrationMethod,
    ComprehensiveRiskExplanation,
)
from ml.explainability.feature_attribution.logistic import LogisticRegressionExplainer
from ml.explainability.feature_attribution.tree_ensemble import GradientBoostingExplainer
from ml.explainability.confidence.calibration import RiskProbabilityCalibrator
from ml.explainability.uncertainty.diagnostics import UncertaintyDiagnostics
from ml.explainability.counterfactual.sensitivity import CounterfactualSensitivityEngine
from ml.risk_model.baseline.logistic_regression.model import BaselineLogisticRegressionModel
from ml.risk_model.contracts import (
    ModelMetadata,
    ModelMode,
    RiskFeatureRecord,
    RiskPredictionClass,
    RiskPredictionOutput,
)
from ml.risk_model.gradient_boosting.model import GradientBoostingRiskModel

router = APIRouter(prefix="/api/v1/risk", tags=["Flood Risk Intelligence"])


ARTIFACTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "ml"
    / "risk_model"
    / "artifacts"
)

MODEL_FILES = {
    "baseline-logistic-regression-v1": ARTIFACTS_DIR / "baseline_logistic_regression_v1.joblib",
    "gradient-boosting-v1": ARTIFACTS_DIR / "gradient_boosting_v1.joblib",
}

_cached_models: Dict[str, Any] = {}


def get_risk_model(model_version: str = "gradient-boosting-v1") -> Any:
    """Loads and caches the requested risk model artifact."""
    if model_version not in MODEL_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown model_version '{model_version}'. Available models: {list(MODEL_FILES.keys())}",
        )

    if model_version not in _cached_models:
        artifact_path = MODEL_FILES[model_version]
        if not artifact_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Risk model artifact for '{model_version}' is not available at {artifact_path}. Please train it first.",
            )
        _cached_models[model_version] = joblib.load(artifact_path)

    return _cached_models[model_version]


class BatchRiskRequest(BaseModel):
    records: List[RiskFeatureRecord]
    mode: ModelMode = Field(default=ModelMode.SIMULATION)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    model_version: str = Field(default="baseline-logistic-regression-v1", description="Model version identifier")


class GeoJsonFeatureProperties(BaseModel):
    sample_id: str
    risk_probability: float
    predicted_class: int
    risk_level: str
    model_version: str
    mode: str
    elevation_m: float
    rainfall_mm_24h: float
    distance_to_river_m: float


@router.post("/predict", response_model=RiskPredictionOutput)
def predict_operational_risk(
    record: RiskFeatureRecord,
    model_version: str = "baseline-logistic-regression-v1",
    mode: ModelMode = ModelMode.SIMULATION,
    threshold: float = 0.5,
):
    """
    Predict operational flood risk for an individual location or facility.
    Returns estimated probability P(risk=1 | features) and local feature contributions.
    """
    try:
        model = get_risk_model(model_version)
        return model.predict_single(record, mode=mode, threshold=threshold)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inference failed: {str(err)}",
        )


@router.post("/batch", response_model=List[RiskPredictionOutput])
def predict_operational_risk_batch(payload: BatchRiskRequest):
    """
    Batch operational flood risk prediction over multiple feature records.
    """
    model = get_risk_model(payload.model_version)
    results = []
    for rec in payload.records:
        try:
            res = model.predict_single(rec, mode=payload.mode, threshold=payload.threshold)
            results.append(res)
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed processing sample '{rec.sample_id}': {str(err)}",
            )
    return results


@router.get("/model-info", response_model=Dict[str, Any])
def get_model_information(model_version: str = "baseline-logistic-regression-v1"):
    """
    Retrieves model version, algorithm, standardized coefficients / feature importances,
    evaluation metrics, and documented limitations.
    """
    model = get_risk_model(model_version)
    if model.metadata:
        return model.metadata.model_dump()
    return {
        "model_version": model.model_version,
        "algorithm": type(model).__name__,
    }


@router.post("/geojson", response_model=Dict[str, Any])
def export_risk_geojson(payload: BatchRiskRequest):
    """
    Evaluates batch features and exports an EPSG:4326 GeoJSON FeatureCollection
    suitable for direct GIS map visualization.
    """
    model = get_risk_model(payload.model_version)
    features = []

    for rec in payload.records:
        pred = model.predict_single(rec, mode=payload.mode, threshold=payload.threshold)
        prob = pred.risk_probability

        if prob >= 0.70:
            level = "CRITICAL"
        elif prob >= 0.40:
            level = "HIGH"
        elif prob >= 0.15:
            level = "MODERATE"
        else:
            level = "LOW"

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [rec.longitude, rec.latitude],
            },
            "properties": {
                "sample_id": rec.sample_id,
                "risk_probability": prob,
                "predicted_class": pred.predicted_class.value,
                "risk_level": level,
                "model_version": model.model_version,
                "mode": payload.mode.value,
                "elevation_m": rec.elevation_m,
                "rainfall_mm_24h": rec.rainfall_mm_24h,
                "distance_to_river_m": rec.distance_to_river_m,
            },
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.post(
    "/explain",
    response_model=ComprehensiveRiskExplanation,
    summary="Generate comprehensive explanation, calibration, uncertainty, and counterfactuals"
)
def explain_operational_risk(
    record: RiskFeatureRecord,
    model_version: str = "baseline-logistic-regression-v1",
    mode: ModelMode = ModelMode.SIMULATION,
    threshold: float = 0.5,
    include_counterfactual: bool = True,
):
    """
    Comprehensive explainability endpoint (Phase 19).
    Generates:
    - Raw prediction and classification
    - Local feature attributions (exact log-odds for LR, tree margin for GB)
    - Global feature signals
    - Calibration status and reliability metrics
    - Uncertainty and distribution status (Mahalanobis centroid distance)
    - Bounded counterfactual sensitivity (what would change the prediction)
    """
    try:
        model = get_risk_model(model_version)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed loading model '{model_version}': {str(err)}",
        )

    # 1. Prediction
    pred_res = model.predict_single(record, mode=mode, threshold=threshold)
    prob = pred_res.risk_probability
    pred_class = pred_res.predicted_class

    # 2. Local & Global Explanation
    if isinstance(model, BaselineLogisticRegressionModel):
        explainer = LogisticRegressionExplainer(model)
    elif isinstance(model, GradientBoostingRiskModel):
        explainer = GradientBoostingExplainer(model)
    else:
        # Fallback if unknown model type wrapped
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No explainer registered for model class {type(model).__name__}",
        )

    pred_id = f"pred-{record.sample_id}"
    local_exp = explainer.explain_local(record, prediction_id=pred_id)
    global_exp = explainer.explain_global()

    # 3. Calibration
    # Initialize calibrator
    calibrator = RiskProbabilityCalibrator(
        base_model=model,
        preprocessor=model.preprocessor,
        method=CalibrationMethod.PLATT_SCALING,
        calibration_version="calib-platt-v1.0",
    )
    calib_res = calibrator.calibrate_probability(prob, record.model_dump())

    # 4. Uncertainty & OOD Diagnostics
    diagnostics = UncertaintyDiagnostics(preprocessor=model.preprocessor)
    uncertainty_report = diagnostics.evaluate_uncertainty(record)

    # 5. Counterfactual Sensitivity
    cf_sensitivity = None
    if include_counterfactual:
        cf_engine = CounterfactualSensitivityEngine(model=model)
        cf_sensitivity = cf_engine.find_counterfactual(record, threshold=threshold)

    return ComprehensiveRiskExplanation(
        prediction_id=pred_id,
        mode=mode,
        model_version=model_version,
        feature_version="v1.0",
        risk_probability=prob,
        predicted_class=pred_class,
        local_explanation=local_exp,
        global_explanation_summary=global_exp.signals,
        calibration=calib_res,
        uncertainty=uncertainty_report,
        counterfactual=cf_sensitivity,
    )

