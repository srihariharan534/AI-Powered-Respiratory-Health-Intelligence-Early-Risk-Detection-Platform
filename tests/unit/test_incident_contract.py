"""
Contract validation tests for Incident schema and Pydantic model.
"""

import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from services.api.app.schemas.incident import Incident

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT_DIR / "data" / "schemas" / "incident.schema.json"
SAMPLE_PATH = ROOT_DIR / "data" / "sample" / "incidents" / "sample_incident.json"


@pytest.fixture
def incident_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_incident_data():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_incident_json_schema_validates_sample(incident_schema, sample_incident_data):
    """Verify sample incident validates against canonical JSON schema."""
    jsonschema.validate(instance=sample_incident_data, schema=incident_schema)


def test_incident_pydantic_validates_sample(sample_incident_data):
    """Verify sample incident parses into Incident Pydantic model."""
    incident = Incident.model_validate(sample_incident_data)
    assert incident.incident_id == "DEMO-INC-001"
    assert incident.severity == "CRITICAL"
    assert incident.location.coordinates == [80.2707, 13.0827]


def test_incident_negative_missing_field(sample_incident_data):
    """Verify missing required field fails validation."""
    invalid = sample_incident_data.copy()
    del invalid["event_type"]
    with pytest.raises(ValidationError):
        Incident.model_validate(invalid)


def test_incident_negative_invalid_severity(sample_incident_data):
    """Verify invalid severity enum fails validation."""
    invalid = sample_incident_data.copy()
    invalid["severity"] = "EXTREME_CATASTROPHE"
    with pytest.raises(ValidationError):
        Incident.model_validate(invalid)


def test_incident_negative_invalid_coordinates(sample_incident_data):
    """Verify longitude outside [-180, 180] fails validation."""
    invalid = sample_incident_data.copy()
    invalid["location"] = {"type": "Point", "coordinates": [250.0, 13.0827]}
    with pytest.raises(ValidationError):
        Incident.model_validate(invalid)
