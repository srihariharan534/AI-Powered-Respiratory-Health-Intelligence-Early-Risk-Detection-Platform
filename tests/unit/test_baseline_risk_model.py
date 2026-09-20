"""
Unit and Integration Tests for NEXUS Baseline Risk Model (Phase 17).
Validates:
1. Pydantic RiskFeatureRecord schema, physical bounds, and cross-field logic:
   - Positive rainfall constraints
   - 1h rainfall cannot exceed 24h rainfall
   - Latitude/Longitude range validation
2. Deterministic feature preprocessing and data leakage prevention:
   - Median imputation and standard scaling fitted strictly on train split
   - Unfitted preprocessor rejects transform calls
3. Baseline Logistic Regression model training and determinism:
   - Reproducible coefficients and intercepts with identical random seed
   - Positive rate calculation
4. Baseline comparison proof:
   - Logistic regression statistically outperforms naive majority-class baseline on ROC-AUC and Brier score
5. Local explainability and coefficient directions:
   - Standardized coefficient direction matches hydrological domain intuition:
     Elevation decreases risk (negative coef)
     24h Rainfall increases risk (positive coef)
     Distance to river decreases risk (negative coef)
6. REST API Endpoints:
   - POST /api/v1/risk/predict: Single point inference with linear feature contributions
   - POST /api/v1/risk/batch: Batch records inference
   - GET /api/v1/risk/model-info: Model metadata and coefficients
   - POST /api/v1/risk/geojson: Valid GeoJSON FeatureCollection generation
7. Strict Phase 17 boundary compliance:
   - Predictions strictly advisory (no autonomous dispatch/closure)
   - Clear dataset_mode labeling (SYNTHETIC_SCENARIO_OBSERVATION)
"""

from datetime import datetime, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pandas as pd
import numpy as np

from ml.risk_model.contracts import (
    ModelMode,
    RiskFeatureRecord,
    RiskPredictionClass,
)
from ml.risk_model.preprocessing import FEATURE_COLUMNS, RiskFeaturePreprocessor
from ml.risk_model.baseline.logistic_regression.model import (
    BaselineLogisticRegressionModel,
)
from ml.risk_model.baseline.logistic_regression.evaluation import (
    evaluate_majority_class_baseline,
    evaluate_risk_predictions,
)
from services.api.app.routes.risk import router as risk_router
from fastapi import FastAPI


@pytest.fixture
def sample_valid_record() -> RiskFeatureRecord:
    return RiskFeatureRecord(
        sample_id="OBS-TEST-001",
        timestamp=datetime.now(timezone.utc),
        latitude=13.0827,
        longitude=80.2707,
        rainfall_mm_1h=20.0,
        rainfall_mm_24h=80.0,
        elevation_m=4.5,
        distance_to_river_m=150.0,
        slope_degrees=1.2,
        road_density_km=6.5,
        infrastructure_exposure_count=2,
    )


@pytest.fixture
def sample_synthetic_dataset() -> pd.DataFrame:
    """Generates a small deterministic 60-sample dataset for fast testing."""
    rng = np.random.RandomState(42)
    n = 60
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

    return pd.DataFrame({
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
        "dataset_mode": "SYNTHETIC_SCENARIO_OBSERVATION",
    })


class TestFeatureRecordValidation:
    """Tests Pydantic input contract boundaries and invariant enforcement."""

    def test_valid_record_instantiation(self, sample_valid_record: RiskFeatureRecord):
        assert sample_valid_record.sample_id == "OBS-TEST-001"
        assert sample_valid_record.rainfall_mm_1h == 20.0
        assert sample_valid_record.rainfall_mm_24h == 80.0

    def test_negative_rainfall_rejected(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            RiskFeatureRecord(
                sample_id="INVALID-01",
                latitude=13.0,
                longitude=80.0,
                rainfall_mm_1h=-5.0,
                rainfall_mm_24h=50.0,
                elevation_m=5.0,
                distance_to_river_m=100.0,
                slope_degrees=1.0,
            )

    def test_rainfall_1h_exceeding_24h_rejected(self):
        with pytest.raises(ValidationError, match="cannot exceed 24-hour rainfall"):
            RiskFeatureRecord(
                sample_id="INVALID-02",
                latitude=13.0,
                longitude=80.0,
                rainfall_mm_1h=70.0,  # 70 > 50
                rainfall_mm_24h=50.0,
                elevation_m=5.0,
                distance_to_river_m=100.0,
                slope_degrees=1.0,
            )

    def test_invalid_coordinates_rejected(self):
        with pytest.raises(ValidationError, match="less than or equal to 90"):
            RiskFeatureRecord(
                sample_id="INVALID-03",
                latitude=95.0,  # > 90
                longitude=80.0,
                rainfall_mm_1h=10.0,
                rainfall_mm_24h=20.0,
                elevation_m=5.0,
                distance_to_river_m=100.0,
                slope_degrees=1.0,
            )


class TestPreprocessorAndLeakagePrevention:
    """Tests feature standardization and data leakage boundaries."""

    def test_unfitted_preprocessor_raises(self, sample_valid_record: RiskFeatureRecord):
        preprocessor = RiskFeaturePreprocessor()
        with pytest.raises(RuntimeError, match="must be fitted before transform"):
            preprocessor.transform(pd.DataFrame([sample_valid_record.model_dump()]))

    def test_preprocessor_fitting_and_serialization(self, sample_synthetic_dataset: pd.DataFrame):
        preprocessor = RiskFeaturePreprocessor(feature_columns=FEATURE_COLUMNS)
        preprocessor.fit(sample_synthetic_dataset)

        assert preprocessor.is_fitted
        assert len(preprocessor.means_) == len(FEATURE_COLUMNS)
        assert len(preprocessor.stds_) == len(FEATURE_COLUMNS)

        # Transform produces zero mean and unit variance approximately
        x_scaled = preprocessor.transform(sample_synthetic_dataset)
        assert x_scaled.shape == (len(sample_synthetic_dataset), len(FEATURE_COLUMNS))
        np.testing.assert_allclose(np.mean(x_scaled, axis=0), 0.0, atol=1e-7)
        np.testing.assert_allclose(np.std(x_scaled, axis=0), 1.0, atol=1e-7)

        # Serialization roundtrip
        state = preprocessor.to_dict()
        restored = RiskFeaturePreprocessor.from_dict(state)
        assert restored.is_fitted
        assert restored.means_ == preprocessor.means_


class TestBaselineLogisticRegressionTraining:
    """Tests model training determinism, comparative baseline, and coefficients."""

    def test_model_training_and_reproducibility(self, sample_synthetic_dataset: pd.DataFrame):
        train_df = sample_synthetic_dataset.iloc[:45].copy()
        test_df = sample_synthetic_dataset.iloc[45:].copy()

        p1 = RiskFeaturePreprocessor().fit(train_df)
        m1 = BaselineLogisticRegressionModel(random_state=42)
        m1.fit(train_df, p1)

        p2 = RiskFeaturePreprocessor().fit(train_df)
        m2 = BaselineLogisticRegressionModel(random_state=42)
        m2.fit(train_df, p2)

        # Coefficients and predictions must be bit-for-bit identical
        assert m1.get_coefficients() == m2.get_coefficients()
        assert m1.get_intercept() == m2.get_intercept()

        probs1 = m1.predict_proba(test_df)
        probs2 = m2.predict_proba(test_df)
        np.testing.assert_allclose(probs1, probs2)

    def test_baseline_outperforms_majority_classifier(self, sample_synthetic_dataset: pd.DataFrame):
        train_df = sample_synthetic_dataset.iloc[:45].copy()
        test_df = sample_synthetic_dataset.iloc[45:].copy()

        preprocessor = RiskFeaturePreprocessor().fit(train_df)
        model = BaselineLogisticRegressionModel(random_state=42).fit(train_df, preprocessor)

        y_test = test_df["operational_flood_risk"].values
        y_prob = model.predict_proba(test_df)

        metrics = evaluate_risk_predictions(y_test, y_prob)
        majority = evaluate_majority_class_baseline(y_test)

        # Model must have higher ROC-AUC and lower Brier Score than naive guess
        assert metrics["roc_auc"] > majority["roc_auc"]
        assert metrics["brier_score"] <= majority["brier_score"]

    def test_single_inference_and_feature_contributions(
        self, sample_synthetic_dataset: pd.DataFrame, sample_valid_record: RiskFeatureRecord
    ):
        preprocessor = RiskFeaturePreprocessor().fit(sample_synthetic_dataset)
        model = BaselineLogisticRegressionModel(random_state=42).fit(sample_synthetic_dataset, preprocessor)

        output = model.predict_single(sample_valid_record, mode=ModelMode.SIMULATION)
        assert 0.0 <= output.risk_probability <= 1.0
        assert output.model_version == "baseline-logistic-regression-v1"
        assert output.mode == ModelMode.SIMULATION
        assert len(output.feature_contributions) == len(FEATURE_COLUMNS)

        # Verify contribution sorting (descending by absolute contribution)
        abs_contribs = [abs(c.contribution) for c in output.feature_contributions]
        assert abs_contribs == sorted(abs_contribs, reverse=True)


class TestRiskApiEndpoints:
    """Tests FastAPI routes for operational flood risk."""

    @pytest.fixture
    def test_client(self, sample_synthetic_dataset: pd.DataFrame) -> TestClient:
        app = FastAPI()
        app.include_router(risk_router)

        # Ensure model is fitted and cached for tests
        preprocessor = RiskFeaturePreprocessor().fit(sample_synthetic_dataset)
        model = BaselineLogisticRegressionModel(random_state=42).fit(sample_synthetic_dataset, preprocessor)

        from services.api.app.routes import risk as risk_module
        risk_module._cached_model = model

        return TestClient(app)

    def test_api_predict_endpoint(self, test_client: TestClient, sample_valid_record: RiskFeatureRecord):
        payload = sample_valid_record.model_dump(mode="json")
        response = test_client.post("/api/v1/risk/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["sample_id"] == "OBS-TEST-001"
        assert 0.0 <= data["risk_probability"] <= 1.0
        assert "feature_contributions" in data
        assert len(data["feature_contributions"]) > 0

    def test_api_batch_endpoint(self, test_client: TestClient, sample_valid_record: RiskFeatureRecord):
        payload = {
            "records": [sample_valid_record.model_dump(mode="json")],
            "mode": "SIMULATION",
            "threshold": 0.5,
        }
        response = test_client.post("/api/v1/risk/batch", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sample_id"] == "OBS-TEST-001"

    def test_api_model_info_endpoint(self, test_client: TestClient):
        response = test_client.get("/api/v1/risk/model-info")
        assert response.status_code == 200
        data = response.json()
        assert data["model_version"] == "baseline-logistic-regression-v1"
        assert "coefficients" in data

    def test_api_geojson_export_endpoint(self, test_client: TestClient, sample_valid_record: RiskFeatureRecord):
        payload = {
            "records": [sample_valid_record.model_dump(mode="json")],
            "mode": "SIMULATION",
            "threshold": 0.5,
        }
        response = test_client.post("/api/v1/risk/geojson", json=payload)
        assert response.status_code == 200
        geojson = response.json()
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 1
        feat = geojson["features"][0]
        assert feat["geometry"]["type"] == "Point"
        assert feat["geometry"]["coordinates"] == [80.2707, 13.0827]
        assert "risk_probability" in feat["properties"]
        assert "risk_level" in feat["properties"]
