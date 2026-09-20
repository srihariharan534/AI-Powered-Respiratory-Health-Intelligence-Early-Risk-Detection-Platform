"""
Contract validation tests for Hospital schema and Pydantic model.
"""

import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from services.api.app.schemas.hospital import Hospital

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT_DIR / "data" / "schemas" / "hospital.schema.json"
SAMPLE_PATH = ROOT_DIR / "data" / "sample" / "hospitals" / "sample_hospital.json"


@pytest.fixture
def hospital_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_hospital_data():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_hospital_json_schema_validates_sample(hospital_schema, sample_hospital_data):
    """Verify sample hospital validates against canonical JSON schema."""
    jsonschema.validate(instance=sample_hospital_data, schema=hospital_schema)


def test_hospital_pydantic_validates_sample(sample_hospital_data):
    """Verify sample hospital parses into Hospital Pydantic model."""
    hosp = Hospital.model_validate(sample_hospital_data)
    assert hosp.hospital_id == "DEMO-HOSP-001"
    assert hosp.capacity == 250
    assert hosp.available_capacity == 34


def test_hospital_negative_available_exceeds_total(sample_hospital_data):
    """Verify available capacity exceeding total capacity is rejected."""
    invalid = sample_hospital_data.copy()
    invalid["available_capacity"] = 300
    with pytest.raises(ValidationError):
        Hospital.model_validate(invalid)
