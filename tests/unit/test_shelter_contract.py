"""
Contract validation tests for Shelter schema and Pydantic model.
"""

import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from services.api.app.schemas.shelter import Shelter

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT_DIR / "data" / "schemas" / "shelter.schema.json"
SAMPLE_PATH = ROOT_DIR / "data" / "sample" / "shelters" / "sample_shelter.json"


@pytest.fixture
def shelter_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_shelter_data():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_shelter_json_schema_validates_sample(shelter_schema, sample_shelter_data):
    """Verify sample shelter validates against canonical JSON schema."""
    jsonschema.validate(instance=sample_shelter_data, schema=shelter_schema)


def test_shelter_pydantic_validates_sample(sample_shelter_data):
    """Verify sample shelter parses into Shelter Pydantic model."""
    shelter = Shelter.model_validate(sample_shelter_data)
    assert shelter.shelter_id == "DEMO-SHELT-001"
    assert shelter.capacity == 500
    assert shelter.available_capacity == 210


def test_shelter_negative_available_exceeds_total(sample_shelter_data):
    """Verify available capacity exceeding total capacity is rejected."""
    invalid = sample_shelter_data.copy()
    invalid["available_capacity"] = 600
    with pytest.raises(ValidationError):
        Shelter.model_validate(invalid)
