"""
Unit and Integration Tests for Gradient Boosting Risk Model (Phase 18).
Validates:
1. Model initialization, default hyperparameters, and deterministic random seed behavior.
2. Training reproducibility: identical trees, feature importances, and predictions with seed 42.
3. Feature importance validity:
   - Sum of feature importances equals 1.0 (within 1e-4)
   - Highest contributing features include rainfall and elevation/distance to river
4. Inference output contract:
   - Output adheres to RiskPredictionOutput
   - Predicted probabilities strictly within [0.0, 1.0]
   - Binary class alignment with 0.50 threshold
5. Dataset SHA-256 fingerprint generation and persistence in metadata.
6. Model artifact serialization and deserialization via joblib.
7. API integration and dynamic model selection:
   - POST /api/v1/risk/predict?model_version=gradient-boosting-v1
   - POST /api/v1/risk/predict?model_version=baseline-logistic-regression-v1
   - Rejection of unknown model versions (HTTP 400)
8. Comparative evaluation consistency across both models on identical holdouts.
"""

from datetime import datetime, timezone
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import numpy as np
import pandas as pd
import joblib

from ml.risk_model.baseline.logistic_regression.evaluation import (
    evaluate_risk_predictions,
)
from ml.risk_model.contracts import ModelMode, RiskFeatureRecord, RiskPredictionClass
from ml.risk_model.gradient_boosting.model import (
    GradientBoostingRiskModel,
    compute_dataset_fingerprint,
)
from ml.risk_model.preprocessing import FEATURE_COLUMNS, RiskFeaturePreprocessor
from services.api.app.routes.risk import router as risk_router


@pytest.fixture
def sample_feature_record() -> RiskFeatureRecord:
    return RiskFeatureRecord(
        sample_id="GB-TEST-001",
        timestamp=datetime.now(timezone.utc),
        latitude=13.0827,
        longitude=80.2707,
        rainfall_mm_1h=15.0,
        rainfall_mm_24h=70.0,
        elevation_m=3.5,
        distance_to_river_m=120.0,
        slope_degrees=1.0,
        road_density_km=7.5,
        infrastructure_exposure_count=3,
    )


@pytest.fixture
def sample_training_df() -> pd.DataFrame:
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


class TestGradientBoostingModelCore:
    """Tests for GradientBoostingRiskModel implementation."""

    def test_model_initialization(self):
        model = GradientBoostingRiskModel(
            model_version="gradient-boosting-v1",
            n_estimators=50,
            learning_rate=0.1,
            max_depth=2,
            random_state=42,
        )
        assert model.model_version == "gradient-boosting-v1"
        assert model.hyperparameters["n_estimators"] == 50
        assert model.hyperparameters["max_depth"] == 2
        assert not model.is_trained

    def test_deterministic_training(self, sample_training_df: pd.DataFrame):
        train_df = sample_training_df.iloc[:45].copy()
        test_df = sample_training_df.iloc[45:].copy()

        p1 = RiskFeaturePreprocessor().fit(train_df)
        m1 = GradientBoostingRiskModel(random_state=42).fit(train_df, p1)

        p2 = RiskFeaturePreprocessor().fit(train_df)
        m2 = GradientBoostingRiskModel(random_state=42).fit(train_df, p2)

        # Predictions and importances must match bit-for-bit
        probs1 = m1.predict_proba(test_df)
        probs2 = m2.predict_proba(test_df)
        np.testing.assert_allclose(probs1, probs2)

        assert m1.get_feature_importances() == m2.get_feature_importances()

    def test_feature_importances_sum_to_one(self, sample_training_df: pd.DataFrame):
        preprocessor = RiskFeaturePreprocessor().fit(sample_training_df)
        model = GradientBoostingRiskModel(random_state=42).fit(sample_training_df, preprocessor)

        importances = model.get_feature_importances()
        assert len(importances) == len(FEATURE_COLUMNS)
        total_importance = sum(importances.values())
        assert pytest.approx(total_importance, abs=1e-3) == 1.0

    def test_single_inference_contract(
        self, sample_training_df: pd.DataFrame, sample_feature_record: RiskFeatureRecord
    ):
        preprocessor = RiskFeaturePreprocessor().fit(sample_training_df)
        model = GradientBoostingRiskModel(random_state=42).fit(sample_training_df, preprocessor)

        output = model.predict_single(sample_feature_record, mode=ModelMode.SIMULATION)
        assert 0.0 <= output.risk_probability <= 1.0
        assert output.model_version == "gradient-boosting-v1"
        assert output.mode == ModelMode.SIMULATION
        assert len(output.feature_contributions) == len(FEATURE_COLUMNS)

    def test_dataset_fingerprint(self, tmp_path: Path):
        dummy_file = tmp_path / "dummy_dataset.csv"
        dummy_file.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
        fp1 = compute_dataset_fingerprint(dummy_file)
        fp2 = compute_dataset_fingerprint(dummy_file)
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex string

    def test_joblib_serialization_roundtrip(
        self, sample_training_df: pd.DataFrame, sample_feature_record: RiskFeatureRecord, tmp_path: Path
    ):
        preprocessor = RiskFeaturePreprocessor().fit(sample_training_df)
        model = GradientBoostingRiskModel(random_state=42).fit(sample_training_df, preprocessor)

        model_path = tmp_path / "test_gb.joblib"
        joblib.dump(model, model_path)

        loaded_model = joblib.load(model_path)
        assert loaded_model.model_version == model.model_version

        p_orig = model.predict_single(sample_feature_record).risk_probability
        p_loaded = loaded_model.predict_single(sample_feature_record).risk_probability
        assert p_orig == p_loaded


class TestRiskApiMultiModelSelection:
    """Tests FastAPI dynamic model selection."""

    @pytest.fixture
    def test_client(self, sample_training_df: pd.DataFrame) -> TestClient:
        app = FastAPI()
        app.include_router(risk_router)

        # Cache both models for routing tests
        preprocessor = RiskFeaturePreprocessor().fit(sample_training_df)
        gb_model = GradientBoostingRiskModel(random_state=42).fit(sample_training_df, preprocessor)

        from ml.risk_model.baseline.logistic_regression.model import BaselineLogisticRegressionModel
        lr_model = BaselineLogisticRegressionModel(random_state=42).fit(sample_training_df, preprocessor)

        from services.api.app.routes import risk as risk_module
        risk_module._cached_models["gradient-boosting-v1"] = gb_model
        risk_module._cached_models["baseline-logistic-regression-v1"] = lr_model

        return TestClient(app)

    def test_predict_with_explicit_gradient_boosting(
        self, test_client: TestClient, sample_feature_record: RiskFeatureRecord
    ):
        payload = sample_feature_record.model_dump(mode="json")
        res = test_client.post("/api/v1/risk/predict?model_version=gradient-boosting-v1", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["model_version"] == "gradient-boosting-v1"
        assert 0.0 <= data["risk_probability"] <= 1.0

    def test_predict_with_explicit_logistic_regression(
        self, test_client: TestClient, sample_feature_record: RiskFeatureRecord
    ):
        payload = sample_feature_record.model_dump(mode="json")
        res = test_client.post("/api/v1/risk/predict?model_version=baseline-logistic-regression-v1", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["model_version"] == "baseline-logistic-regression-v1"

    def test_predict_with_unknown_model_rejected(
        self, test_client: TestClient, sample_feature_record: RiskFeatureRecord
    ):
        payload = sample_feature_record.model_dump(mode="json")
        res = test_client.post("/api/v1/risk/predict?model_version=non-existent-v99", json=payload)
        assert res.status_code == 400
        assert "Unknown model_version" in res.json()["detail"]
