"""
Unit tests for Hazard-Agnostic Multi-Emergency Core and Domain Modules.
Verifies all 12 disaster domains, risk evaluation, and maturity reporting.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.app.routes.hazards import router as hazards_router
from services.hazards.contracts import (
    EmergencyEvent,
    EmergencySeverity,
    EmergencyStatus,
    EmergencyType,
    ModuleMaturity,
)
from services.hazards.registry import HazardRegistry


def test_hazard_registry_all_12_emergencies():
    registry = HazardRegistry()
    supported = registry.list_supported_emergencies()
    assert len(supported) == 13  # 12 required + severe storm distinction

    types = [item["emergency_type"] for item in supported]
    assert EmergencyType.FLOOD.value in types
    assert EmergencyType.CYCLONE.value in types
    assert EmergencyType.LANDSLIDE.value in types
    assert EmergencyType.WILDFIRE.value in types
    assert EmergencyType.EXTREME_HEAT.value in types
    assert EmergencyType.EARTHQUAKE.value in types
    assert EmergencyType.INDUSTRIAL_ACCIDENT.value in types
    assert EmergencyType.CHEMICAL_INCIDENT.value in types
    assert EmergencyType.URBAN_INFRASTRUCTURE_FAILURE.value in types
    assert EmergencyType.PUBLIC_HEALTH_EMERGENCY.value in types
    assert EmergencyType.MAJOR_TRANSPORT_INCIDENT.value in types


def test_flood_hazard_module_risk():
    registry = HazardRegistry()
    mod = registry.get_module(EmergencyType.FLOOD)
    assert mod.get_maturity() == ModuleMaturity.VALIDATED

    event = EmergencyEvent(
        emergency_id="EMG-FLOOD-01",
        emergency_type=EmergencyType.FLOOD,
        severity=EmergencySeverity.HIGH,
        status=EmergencyStatus.ACTIVE,
        location={"type": "Point", "coordinates": [80.22, 13.01]},
        observations={"water_depth_m": 1.5, "rainfall_mm": 180.0},
    )
    res = mod.calculate_risk(event, {})
    assert res.risk_score >= 0.5
    assert res.hazard_type == EmergencyType.FLOOD
    assert "BOAT" in mod.get_required_resources(event)


def test_cyclone_hazard_module_risk():
    registry = HazardRegistry()
    mod = registry.get_module(EmergencyType.CYCLONE)
    assert mod.get_maturity() == ModuleMaturity.IMPLEMENTED

    event = EmergencyEvent(
        emergency_id="EMG-CYC-01",
        emergency_type=EmergencyType.CYCLONE,
        severity=EmergencySeverity.CRITICAL,
        status=EmergencyStatus.ACTIVE,
        location={"type": "Point", "coordinates": [80.25, 13.04]},
        observations={"wind_speed_kmh": 145.0},
    )
    res = mod.calculate_risk(event, {})
    assert res.risk_score >= 0.6
    assert "TREE_CLEARANCE_CREW" in mod.get_required_resources(event)


def test_earthquake_hazard_module_risk():
    registry = HazardRegistry()
    mod = registry.get_module(EmergencyType.EARTHQUAKE)
    event = EmergencyEvent(
        emergency_id="EMG-EQ-01",
        emergency_type=EmergencyType.EARTHQUAKE,
        severity=EmergencySeverity.CRITICAL,
        status=EmergencyStatus.ACTIVE,
        location={"type": "Point", "coordinates": [80.20, 13.00]},
        observations={"magnitude": 6.8},
    )
    res = mod.calculate_risk(event, {})
    assert res.risk_score >= 0.7
    assert "FIELD_HOSPITAL" in mod.get_required_resources(event)


def test_hazard_rest_api():
    app = FastAPI()
    app.include_router(hazards_router)
    client = TestClient(app)

    # List all
    resp = client.get("/api/v1/hazards")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 12

    # Evaluate endpoint
    event_payload = {
        "emergency_id": "EMG-HEAT-01",
        "emergency_type": "EXTREME_HEAT",
        "severity": "CRITICAL",
        "status": "ACTIVE",
        "location": {"type": "Point", "coordinates": [80.22, 13.01]},
        "observations": {"heat_index_c": 48.0},
    }
    resp_eval = client.post("/api/v1/hazards/evaluate", json=event_payload)
    assert resp_eval.status_code == 200
    res_data = resp_eval.json()
    assert res_data["hazard_type"] == "EXTREME_HEAT"
    assert res_data["risk_score"] >= 0.7
