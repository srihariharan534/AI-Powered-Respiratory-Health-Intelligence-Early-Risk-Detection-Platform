"""
Contract validation tests for Recommendation schema and Pydantic model.
"""

import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from services.api.app.schemas.recommendation import Recommendation

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT_DIR / "data" / "schemas" / "recommendation.schema.json"
SAMPLE_PATH = (
    ROOT_DIR
    / "data"
    / "sample"
    / "recommendations"
    / "sample_recommendation.json"
)


@pytest.fixture
def recommendation_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_recommendation_data():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_recommendation_json_schema_validates_sample(
    recommendation_schema, sample_recommendation_data
):
    """Verify sample recommendation validates against canonical JSON schema."""
    jsonschema.validate(
        instance=sample_recommendation_data, schema=recommendation_schema
    )


def test_recommendation_pydantic_validates_sample(sample_recommendation_data):
    """Verify sample recommendation parses into Recommendation Pydantic model."""
    rec = Recommendation.model_validate(sample_recommendation_data)
    assert rec.recommendation_id == "DEMO-REC-001"
    assert rec.action == "DIVERT_AMBULANCES"
    assert rec.requires_human_approval is True
    assert rec.approval_status == "PENDING"
    assert rec.confidence == 0.92


def test_recommendation_negative_invalid_confidence_range(
    sample_recommendation_data,
):
    """Verify confidence > 1.0 fails validation."""
    invalid = sample_recommendation_data.copy()
    invalid["confidence"] = 1.45
    with pytest.raises(ValidationError):
        Recommendation.model_validate(invalid)


def test_recommendation_negative_disabling_human_approval(
    sample_recommendation_data,
):
    """Verify attempting to set requires_human_approval to False fails validation."""
    invalid = sample_recommendation_data.copy()
    invalid["requires_human_approval"] = False
    with pytest.raises(ValidationError):
        Recommendation.model_validate(invalid)
