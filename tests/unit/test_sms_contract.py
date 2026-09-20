"""
Contract validation tests for SMS schema and Pydantic model.
"""

import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from services.api.app.schemas.sms import SMSMessage

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT_DIR / "data" / "schemas" / "sms.schema.json"
SAMPLE_PATH = ROOT_DIR / "data" / "sample" / "sms" / "sample_sms.json"


@pytest.fixture
def sms_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_sms_data():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_sms_json_schema_validates_sample(sms_schema, sample_sms_data):
    """Verify sample SMS validates against canonical JSON schema."""
    jsonschema.validate(instance=sample_sms_data, schema=sms_schema)


def test_sms_pydantic_validates_sample(sample_sms_data):
    """Verify sample SMS parses into SMSMessage Pydantic model."""
    sms = SMSMessage.model_validate(sample_sms_data)
    assert sms.message_id == "DEMO-SMS-001"
    assert sms.event_type == "FLOOD"
    assert sms.status == "BLOCKED"
    assert sms.longitude == 80.2707
    assert sms.latitude == 13.0827


def test_sms_negative_message_exceeds_160_chars(sample_sms_data):
    """Verify raw SMS exceeding 160 character boundary fails validation."""
    invalid = sample_sms_data.copy()
    invalid["raw_message"] = "X" * 165
    with pytest.raises(ValidationError):
        SMSMessage.model_validate(invalid)
