"""
Unit tests for Emergency SMS Fallback Parsing, Ingestion, and Simulator (Phase 26).
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.repositories.incident_service import IncidentService
from services.api.app.routes.sms import router as sms_router
from services.sms.contracts import SMSEventType, SMSSeverity, SMSSource, SMSStatus
from services.sms.ingestion import SMSIngestionService
from services.sms.parser import SMSParser


def test_sms_parser_valid_message():
    raw = "FLOOD ROAD-12 BLOCKED HIGH 13.08 80.27"
    res = SMSParser.parse(raw, sender_reference="RESCUE_TEAM_4")
    assert res.is_valid is True
    assert res.parsed_message is not None
    msg = res.parsed_message
    assert msg.event_type == SMSEventType.FLOOD
    assert msg.entity_id == "ROAD-12"
    assert msg.status == SMSStatus.BLOCKED
    assert msg.severity == SMSSeverity.HIGH
    assert msg.latitude == 13.08
    assert msg.longitude == 80.27
    assert msg.sender_reference == "RESCUE_TEAM_4"


def test_sms_parser_invalid_tokens():
    raw = "FLOOD ROAD-12 BLOCKED"
    res = SMSParser.parse(raw)
    assert res.is_valid is False
    assert "Insufficient SMS tokens" in res.error_message


def test_sms_parser_out_of_bounds_coordinates():
    raw = "FLOOD ROAD-12 BLOCKED HIGH 95.0 190.0"
    res = SMSParser.parse(raw)
    assert res.is_valid is False
    assert "latitude" in res.field_errors
    assert "longitude" in res.field_errors


def test_sms_ingestion_duplicate_rejection():
    dt = DigitalTwinStateManager(initial_version=1)
    incident_service = IncidentService(digital_twin=dt)
    service = SMSIngestionService(incident_service=incident_service, digital_twin=dt)

    raw = "FLOOD CANAL-01 OPEN CRITICAL 13.0180 80.2230"
    res1 = service.ingest_sms(raw)
    assert res1.success is True
    assert res1.status == "INGESTED"
    assert res1.incident_id is not None

    # Re-submitting identical SMS triggers duplicate rejection
    res2 = service.ingest_sms(raw)
    assert res2.is_duplicate is True
    assert res2.status == "DUPLICATE_REJECTED"


def test_sms_ingestion_rest_endpoint():
    app = FastAPI()
    app.include_router(sms_router)
    client = TestClient(app)

    # Valid ingestion
    req = {
        "raw_message": "MEDICAL SHELTER-4 FULL HIGH 13.02 80.23",
        "sender_reference": "STATION_CHIEF_01",
        "simulated": True,
    }
    resp = client.post("/api/v1/sms/ingest", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "INGESTED"
    assert data["incident_id"] is not None

    # Invalid syntax returns 422
    bad_req = {
        "raw_message": "NOT_AN_SMS",
        "sender_reference": "STATION_CHIEF_01",
    }
    resp_bad = client.post("/api/v1/sms/ingest", json=bad_req)
    assert resp_bad.status_code == 422
