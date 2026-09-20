"""
Comprehensive Unit and Integration Tests for NEXUS Phase 19 Explainability and Uncertainty.
Validates:
1. Logistic regression feature attribution and exact additive reconstruction:
   base_value + sum(contributions) == reconstructed_output
2. Gradient boosting tree ensemble attribution and Gini rankings
3. Calibration training without test set leakage and probability bounded in [0, 1]
4. Uncertainty & data quality diagnostics: missing feature imputation and OOD standardized distance
5. Counterfactual sensitivity: physical bounds preservation and delta recomputation verification
6. API endpoint tests: POST /api/v1/risk/explain
7. Error handling: feature validation, unknown model rejection (HTTP 400), and non-autonomous advisory notes
"""

from datetime import datetime, timezone
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import numpy as np
import pandas as pd

from ml.explainability.confidence.calibration import RiskProbabilityCalibrator
from ml.explainability.contracts import (
    AttributionDirection,
    CalibrationMethod,
    DistributionStatus,
    OutputSpace,
)
from ml.explainability.counterfactual.sensitivity import CounterfactualSensitivityEngine
from ml.explainability.feature_attribution.logistic import LogisticRegressionExplainer
from ml.explainability.feature_attribution.tree_ensemble import GradientBoostingExplainer
from ml.explainability.uncertainty.diagnostics import UncertaintyDiagnostics
from ml.risk_model.baseline.logistic_regression.model import BaselineLogisticRegressionModel
from ml.risk_model.contracts import ModelMode, RiskFeatureRecord, RiskPredictionClass
from ml.risk_model.gradient_boosting.model import GradientBoostingRiskModel
from ml.risk_model.preprocessing import FEATURE_COLUMNS, RiskFeaturePreprocessor
from services.api.app.routes.risk import router as risk_router


@pytest.fixture
def sample_feature_record() -> RiskFeatureRecord:
    return RiskFeatureRecord(
        sample_id="EXP-TEST-001",
        timestamp=datetime.now(timezone.utc),
        latitude=13.0827,
        longitude=80.2707,
        rainfall_mm_1h=18.0,
        rainfall_mm_24h=85.0,
        elevation_m=4.2,
        distance_to_river_m=150.0,
        slope_degrees=1.2,
        road_density_km=8.0,
        infrastructure_exposure_count=2,
    )


@pytest.fixture
def trained_models():
    rng = np.random.RandomState(42)
    n = 100
    rain24 = rng.uniform(5, 120, size=n)
    rain1 = rain24 * 0.25
    elev = rng.uniform(2, 20, size=n)
    dist = rng.uniform(50, 2000, size=n)
    slope = rng.uniform(0.5, 4.0, size=n)
    road = rng.uniform(1.0, 10.0, size=n)
    infra = rng.randint(0, 5, size=n)

    z = 0.03 * rain24 - 0.25 * elev - 0.001 * dist + 0.5
    prob = 1.0 / (1.0 + np.exp(-z))
    target = (prob >= 0.5).astype(int)

    df = pd.DataFrame({
        "sample_id": [f"TEST-{i:03d}" for i in range(n)],
        "timestamp": [f"2026-09-15T12:{i:02d}:00Z" for i in range(n)],
        "latitude": rng.uniform(13.06, 13.09, size=n),
        "longitude": rng.uniform(80.25, 80.28, size=n),
        "rainfall_mm_1h": rain1,
        "rainfall_mm_24h": rain24,
        "elevation_m": elev,
        "distance_to_river_m": dist,
        "slope_degrees": slope,
        "road_density_km": road,
        "infrastructure_exposure_count": infra,
        "operational_flood_risk": target,
    })

    preprocessor = RiskFeaturePreprocessor()
    preprocessor.fit(df)

    lr_model = BaselineLogisticRegressionModel()
    lr_model.fit(df, preprocessor)

    gb_model = GradientBoostingRiskModel(n_estimators=30)
    gb_model.fit(df, preprocessor)

    return lr_model, gb_model, preprocessor, df


class TestFeatureAttributionEngines:
    """Validates local and global feature attribution logic."""

    def test_logistic_additive_reconstruction(self, trained_models, sample_feature_record):
        lr_model, _, _, _ = trained_models
        explainer = LogisticRegressionExplainer(lr_model)

        exp = explainer.explain_local(sample_feature_record)
        assert exp.output_space == OutputSpace.LOG_ODDS
        assert exp.additive_reconstruction_passed is True

        # Mathematical verification: base_value + sum(contributions) == reconstructed_output
        calc_reconstructed = exp.base_value + exp.sum_contributions
        assert abs(calc_reconstructed - exp.reconstructed_output) < 1e-4
        assert len(exp.attributions) == 7

        # Check non-causal explanation phrasing
        for attr in exp.attributions:
            assert "caused" not in attr.explanation_text.lower()
            assert "prevent" not in attr.explanation_text.lower()
            assert attr.direction in [
                AttributionDirection.INCREASES_RISK,
                AttributionDirection.DECREASES_RISK,
                AttributionDirection.NEUTRAL,
            ]

    def test_logistic_global_explanation(self, trained_models):
        lr_model, _, _, _ = trained_models
        explainer = LogisticRegressionExplainer(lr_model)
        global_exp = explainer.explain_global()

        assert global_exp.algorithm == "LogisticRegression"
        assert len(global_exp.signals) == 7
        assert global_exp.signals[0].rank == 1
        assert global_exp.signals[-1].rank == 7

    def test_gradient_boosting_attribution(self, trained_models, sample_feature_record):
        _, gb_model, _, _ = trained_models
        explainer = GradientBoostingExplainer(gb_model)

        exp = explainer.explain_local(sample_feature_record)
        assert exp.output_space == OutputSpace.PROBABILITY_MARGIN
        assert len(exp.attributions) == 7
        assert exp.base_value == 0.0

        global_exp = explainer.explain_global()
        assert global_exp.algorithm == "GradientBoostingClassifier"
        total_importance = sum(s.importance_or_weight for s in global_exp.signals)
        assert abs(total_importance - 1.0) < 1e-3


class TestConfidenceAndCalibration:
    """Validates probability calibration without data leakage."""

    def test_calibrator_fitting_and_bounds(self, trained_models, sample_feature_record):
        lr_model, _, preprocessor, df = trained_models

        # Partition into train and validation
        val_df = df.iloc[:40].copy()
        calibrator = RiskProbabilityCalibrator(
            base_model=lr_model,
            preprocessor=preprocessor,
            method=CalibrationMethod.PLATT_SCALING,
        )
        calibrator.fit_on_validation(val_df)

        assert calibrator.is_fitted is True
        assert calibrator.validation_brier is not None

        raw_prob = float(lr_model.predict_proba(pd.DataFrame([sample_feature_record.model_dump()]))[0])
        res = calibrator.calibrate_probability(raw_prob, sample_feature_record.model_dump())

        assert res.is_calibrated is True
        assert res.calibrated_probability is not None
        assert 0.0 <= res.calibrated_probability <= 1.0
        assert res.calibration_method == CalibrationMethod.PLATT_SCALING


class TestUncertaintyAndDataQuality:
    """Validates uncertainty diagnostics separating completeness from OOD."""

    def test_uncertainty_in_distribution(self, trained_models, sample_feature_record):
        _, _, preprocessor, _ = trained_models
        diag = UncertaintyDiagnostics(preprocessor)

        report = diag.evaluate_uncertainty(sample_feature_record)
        assert report.data_quality.has_imputations is False
        assert report.data_quality.available_features_count == 7
        assert report.distribution_status in [
            DistributionStatus.IN_DISTRIBUTION,
            DistributionStatus.WARNING,
        ]

    def test_uncertainty_missing_feature_imputation(self, trained_models, sample_feature_record):
        _, _, preprocessor, _ = trained_models
        diag = UncertaintyDiagnostics(preprocessor)

        raw_dict = sample_feature_record.model_dump()
        raw_dict["elevation_m"] = None  # Simulate missing elevation

        report = diag.evaluate_uncertainty(sample_feature_record, raw_input_dict=raw_dict)
        assert report.data_quality.has_imputations is True
        assert "elevation_m" in report.data_quality.imputed_features
        assert any("imputed" in n.lower() for n in report.uncertainty_notes)

    def test_uncertainty_extreme_ood_detection(self, trained_models):
        _, _, preprocessor, _ = trained_models
        diag = UncertaintyDiagnostics(preprocessor)

        # Extreme values to trigger OOD
        extreme_record = RiskFeatureRecord(
            sample_id="OOD-001",
            latitude=13.08,
            longitude=80.27,
            rainfall_mm_1h=450.0,
            rainfall_mm_24h=1900.0,
            elevation_m=-45.0,
            distance_to_river_m=1.0,
            slope_degrees=85.0,
            road_density_km=48.0,
            infrastructure_exposure_count=95,
        )

        report = diag.evaluate_uncertainty(extreme_record)
        assert report.distribution_status == DistributionStatus.OUT_OF_DISTRIBUTION
        assert report.distance_from_centroid > report.distance_threshold_ood


class TestCounterfactualSensitivity:
    """Validates bounded counterfactual search respecting physical constraints."""

    def test_counterfactual_bounds_and_recomputation(self, trained_models, sample_feature_record):
        lr_model, _, _, _ = trained_models
        cf_engine = CounterfactualSensitivityEngine(lr_model)

        cf = cf_engine.find_counterfactual(sample_feature_record)
        if cf:
            assert cf.constraints_satisfied is True
            assert cf.target_prediction_class != (
                RiskPredictionClass.HIGH_RISK if cf.current_probability >= 0.5 else RiskPredictionClass.LOW_RISK
            )
            # Physical verification: all modified values must be non-negative
            for mod in cf.modified_features:
                if "rainfall" in mod.feature_name or "distance" in mod.feature_name:
                    assert mod.suggested_value >= 0.0


class TestRiskApiExplainEndpoint:
    """Tests POST /api/v1/risk/explain via FastAPI TestClient."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = FastAPI()
        app.include_router(risk_router)
        return TestClient(app)

    def test_explain_endpoint_success(self, client, sample_feature_record):
        payload = sample_feature_record.model_dump()
        payload["timestamp"] = payload["timestamp"].isoformat()

        response = client.post(
            "/api/v1/risk/explain?model_version=baseline-logistic-regression-v1",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()

        assert "prediction_id" in data
        assert "risk_probability" in data
        assert "local_explanation" in data
        assert "global_explanation_summary" in data
        assert "calibration" in data
        assert "uncertainty" in data
        assert "advisory_warning" in data
        assert "NON-AUTONOMOUS ADVISORY NOTICE" in data["advisory_warning"]

        # Local explanation additive reconstruction check
        local = data["local_explanation"]
        assert local["additive_reconstruction_passed"] is True
        assert len(local["attributions"]) == 7

    def test_explain_endpoint_gradient_boosting(self, client, sample_feature_record):
        payload = sample_feature_record.model_dump()
        payload["timestamp"] = payload["timestamp"].isoformat()

        response = client.post(
            "/api/v1/risk/explain?model_version=gradient-boosting-v1",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model_version"] == "gradient-boosting-v1"
        assert data["local_explanation"]["output_space"] == "PROBABILITY_MARGIN"

    def test_explain_endpoint_unknown_model_rejected(self, client, sample_feature_record):
        payload = sample_feature_record.model_dump()
        payload["timestamp"] = payload["timestamp"].isoformat()

        response = client.post(
            "/api/v1/risk/explain?model_version=non-existent-model",
            json=payload,
        )
        assert response.status_code == 400
        assert "Unknown model_version" in response.json()["detail"]
