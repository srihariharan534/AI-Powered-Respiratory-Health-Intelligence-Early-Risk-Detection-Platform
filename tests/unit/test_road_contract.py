"""
Contract validation tests for Road schema and Pydantic model.
"""

import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from services.api.app.schemas.road import Road

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT_DIR / "data" / "schemas" / "road.schema.json"
SAMPLE_PATH = ROOT_DIR / "data" / "sample" / "roads" / "sample_road.json"


@pytest.fixture
def road_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_road_data():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_road_json_schema_validates_sample(road_schema, sample_road_data):
    """Verify sample road validates against canonical JSON schema."""
    jsonschema.validate(instance=sample_road_data, schema=road_schema)


def test_road_pydantic_validates_sample(sample_road_data):
    """Verify sample road parses into Road Pydantic model."""
    road = Road.model_validate(sample_road_data)
    assert road.road_id == "DEMO-ROAD-101"
    assert road.road_type == "bridge"
    assert road.status == "BLOCKED"


def test_road_negative_invalid_status(sample_road_data):
    """Verify invalid status fails validation."""
    invalid = sample_road_data.copy()
    invalid["status"] = "WASHED_OUT"
    with pytest.raises(ValidationError):
        Road.model_validate(invalid)
