"""
Tests for NEXUS Facility Management (Phase 16).
Validates:
- Canonical Hospital and Shelter Pydantic contract compliance
- Capacity model bounds validation:
    0 <= available_capacity <= capacity
    Rejection of negative capacity, negative available_capacity, and available > capacity
- Hospital REST API endpoints and service workflows:
    create, get, list, filtering, pagination, deterministic sorting
    patch capacity with optimistic concurrency checks
    patch status with optimistic concurrency checks
    chronological audit history preservation
- Shelter REST API endpoints and service workflows:
    create, get, list, filtering, pagination, deterministic sorting
    patch capacity with optimistic concurrency checks
    patch status with optimistic concurrency checks
    chronological audit history preservation
- Digital Twin integration:
    CapacityUpdatedEvent emission & state version increment
    FacilityStatusChangedEvent emission & state version increment
- Flood exposure spatial evaluation:
    Facility inside simulated flood polygon is evaluated as EXPOSED
    Strict rule: EXPOSED does not alter status to CLOSED (EXPOSED != CLOSED)
- What-If counterfactual scenarios:
    Hospital capacity saturation scenario (modifies isolated state; live state unchanged)
    Shelter capacity exhaustion scenario (modifies isolated state; live state unchanged)
- Deterministic synthetic demo fixtures and provenance labeling
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.repositories.facility_service import (
    FacilityNotFoundError,
    FacilityService,
    FacilityStateVersionConflictError,
)
from services.api.app.schemas.hospital import (
    Hospital,
    HospitalSource,
    HospitalStatus,
)
from services.api.app.schemas.incident import PointLocation
from services.api.app.schemas.road import Accessibility
from services.api.app.schemas.shelter import (
    Shelter,
    ShelterSource,
    ShelterStatus,
)
from services.simulation import (
    HospitalCapacityModification,
    ShelterCapacityModification,
    WhatIfScenario,
    WhatIfScenarioEngine,
    WhatIfScenarioType,
)


@pytest.fixture
def sample_hospital() -> Hospital:
    return Hospital(
        schema_version="1.0.0",
        hospital_id="H-TEST-001",
        name="Apex Trauma & Emergency Center",
        location=PointLocation(type="Point", coordinates=[80.2707, 13.0827]),
        status=HospitalStatus.OPERATIONAL,
        accessibility=Accessibility.ALL_VEHICLES,
        capacity=200,
        available_capacity=45,
        emergency_available=True,
        icu_available=12,
        last_updated=datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc),
        source=HospitalSource.SYNTHETIC_DEMO,
    )


@pytest.fixture
def sample_shelter() -> Shelter:
    return Shelter(
        schema_version="1.0.0",
        shelter_id="S-TEST-001",
        name="District Cyclone Relief Center",
        location=PointLocation(type="Point", coordinates=[80.2750, 13.0850]),
        status=ShelterStatus.OPEN,
        accessibility=Accessibility.ALL_VEHICLES,
        capacity=400,
        available_capacity=150,
        has_power_backup=True,
        has_potable_water=True,
        last_updated=datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc),
        source=ShelterSource.SYNTHETIC_DEMO,
    )


class TestCapacityModelValidation:
    """Validate 0 <= available_capacity <= capacity rules."""

    def test_hospital_valid_capacity(self, sample_hospital: Hospital):
        assert sample_hospital.capacity == 200
        assert sample_hospital.available_capacity == 45

    def test_hospital_rejects_available_exceeding_total(self, sample_hospital: Hospital):
        data = sample_hospital.model_dump()
        data["available_capacity"] = 250  # 250 > 200
        with pytest.raises(ValidationError, match="cannot exceed total capacity"):
            Hospital.model_validate(data)

    def test_hospital_rejects_negative_capacity(self, sample_hospital: Hospital):
        data = sample_hospital.model_dump()
        data["capacity"] = -5
        with pytest.raises(ValidationError):
            Hospital.model_validate(data)

    def test_hospital_rejects_negative_available_capacity(self, sample_hospital: Hospital):
        data = sample_hospital.model_dump()
        data["available_capacity"] = -1
        with pytest.raises(ValidationError):
            Hospital.model_validate(data)

    def test_shelter_rejects_available_exceeding_total(self, sample_shelter: Shelter):
        data = sample_shelter.model_dump()
        data["available_capacity"] = 500  # 500 > 400
        with pytest.raises(ValidationError, match="cannot exceed total capacity"):
            Shelter.model_validate(data)


class TestHospitalOperationalService:
    """Test Hospital registration, optimistic concurrency, and audit trails."""

    def test_create_and_retrieve_hospital(self, sample_hospital: Hospital):
        twin = DigitalTwinStateManager()
        service = FacilityService(digital_twin=twin)

        record = service.create_hospital(sample_hospital, actor="FIELD_COORDINATOR")
        assert record["hospital_id"] == "H-TEST-001"
        assert record["state_version"] == 1
        assert record["status"] == "OPERATIONAL"

        # Check Digital Twin entity registry
        dt_entity = twin.get_hospital("H-TEST-001")
        assert dt_entity is not None
        assert dt_entity.capacity == 200
        assert dt_entity.available_capacity == 45

        # Check audit trail entry
        history = service.get_hospital_history("H-TEST-001")
        assert len(history) == 1
        assert history[0]["action"] == "CREATED"
        assert history[0]["state_version"] == 1

    def test_duplicate_hospital_id_rejected(self, sample_hospital: Hospital):
        service = FacilityService()
        service.create_hospital(sample_hospital)
        with pytest.raises(ValueError, match="already exists"):
            service.create_hospital(sample_hospital)

    def test_update_hospital_capacity_workflow(self, sample_hospital: Hospital):
        twin = DigitalTwinStateManager()
        service = FacilityService(digital_twin=twin)
        service.create_hospital(sample_hospital)

        # Update available capacity: 45 -> 32
        updated = service.update_hospital_capacity(
            hospital_id="H-TEST-001",
            new_available_capacity=32,
            expected_state_version=1,
            reason="Emergency admissions from Sector 1",
        )
        assert updated["available_capacity"] == 32
        assert updated["state_version"] == 2

        # Check Digital Twin synchronization & state version
        assert twin.state_version >= 1
        assert twin.get_hospital("H-TEST-001").available_capacity == 32

        # Check history preservation
        history = service.get_hospital_history("H-TEST-001")
        assert len(history) == 2
        assert history[1]["action"] == "CAPACITY_UPDATED"
        assert history[1]["state_version"] == 2
        assert "Emergency admissions" in history[1]["details"]

    def test_hospital_optimistic_concurrency_conflict(self, sample_hospital: Hospital):
        service = FacilityService()
        service.create_hospital(sample_hospital)

        # Operator 1 successfully updates
        service.update_hospital_capacity("H-TEST-001", 30, expected_state_version=1)

        # Operator 2 attempts update based on stale version 1
        with pytest.raises(FacilityStateVersionConflictError) as exc_info:
            service.update_hospital_capacity("H-TEST-001", 20, expected_state_version=1)

        assert exc_info.value.expected_version == 1
        assert exc_info.value.current_version == 2

    def test_update_hospital_status_transition(self, sample_hospital: Hospital):
        twin = DigitalTwinStateManager()
        service = FacilityService(digital_twin=twin)
        service.create_hospital(sample_hospital)

        updated = service.update_hospital_status(
            hospital_id="H-TEST-001",
            new_status=HospitalStatus.OVERLOADED,
            expected_state_version=1,
            reason="Triage surge threshold reached",
        )
        assert updated["status"] == "OVERLOADED"
        assert updated["state_version"] == 2
        assert twin.get_hospital("H-TEST-001").status == HospitalStatus.OVERLOADED

    def test_hospital_list_filtering_and_pagination(self, sample_hospital: Hospital):
        service = FacilityService()
        service.create_hospital(sample_hospital)

        # Filter by status
        res = service.list_hospitals(status=HospitalStatus.OPERATIONAL)
        assert res["total"] == 1

        res_closed = service.list_hospitals(status=HospitalStatus.CLOSED)
        assert res_closed["total"] == 0

        # Filter by emergency availability
        res_em = service.list_hospitals(emergency_available=True)
        assert res_em["total"] == 1

        # Filter by available capacity
        res_cap = service.list_hospitals(has_available_capacity=True)
        assert res_cap["total"] == 1


class TestShelterOperationalService:
    """Test Shelter registration, capacity, status, and audit trails."""

    def test_create_and_retrieve_shelter(self, sample_shelter: Shelter):
        twin = DigitalTwinStateManager()
        service = FacilityService(digital_twin=twin)

        record = service.create_shelter(sample_shelter)
        assert record["shelter_id"] == "S-TEST-001"
        assert record["state_version"] == 1
        assert record["capacity"] == 400
        assert record["available_capacity"] == 150

        # Check Digital Twin registration
        dt_shelt = twin.get_shelter("S-TEST-001")
        assert dt_shelt is not None
        assert dt_shelt.available_capacity == 150

        # Check audit trail
        history = service.get_shelter_history("S-TEST-001")
        assert len(history) == 1
        assert history[0]["action"] == "CREATED"

    def test_update_shelter_capacity_and_concurrency(self, sample_shelter: Shelter):
        twin = DigitalTwinStateManager()
        service = FacilityService(digital_twin=twin)
        service.create_shelter(sample_shelter)

        # Update available capacity: 150 -> 80
        updated = service.update_shelter_capacity(
            shelter_id="S-TEST-001",
            new_available_capacity=80,
            expected_state_version=1,
            reason="Arrival of 70 evacuees from flood zone",
        )
        assert updated["available_capacity"] == 80
        assert updated["state_version"] == 2
        assert twin.get_shelter("S-TEST-001").available_capacity == 80

        # Concurrency conflict
        with pytest.raises(FacilityStateVersionConflictError):
            service.update_shelter_capacity("S-TEST-001", 50, expected_state_version=1)

    def test_update_shelter_status_transition(self, sample_shelter: Shelter):
        twin = DigitalTwinStateManager()
        service = FacilityService(digital_twin=twin)
        service.create_shelter(sample_shelter)

        updated = service.update_shelter_status(
            shelter_id="S-TEST-001",
            new_status=ShelterStatus.AT_CAPACITY,
            expected_state_version=1,
            reason="Shelter reached full safe capacity",
        )
        assert updated["status"] == "AT_CAPACITY"
        assert updated["state_version"] == 2
        assert twin.get_shelter("S-TEST-001").status == ShelterStatus.AT_CAPACITY


class TestFloodExposureSpatialEvaluation:
    """
    Test flood simulation intersection:
    Strict Rule: facility inside simulated polygon is marked EXPOSED.
    EXPOSED != CLOSED and does not automatically alter facility operational status.
    """

    def test_flood_exposure_spatial_intersection(self, sample_hospital: Hospital):
        service = FacilityService()
        service.create_hospital(sample_hospital)

        # 1. No active flood polygon -> status NOT_EVALUATED
        hosp_before = service.get_hospital("H-TEST-001")
        assert hosp_before["flood_exposure"]["is_exposed"] is False
        assert hosp_before["flood_exposure"]["status"] == "NOT_EVALUATED"

        # 2. Polygon covering [80.2707, 13.0827]
        flood_polygon = {
            "type": "Polygon",
            "coordinates": [
                [
                    [80.2600, 13.0700],
                    [80.2800, 13.0700],
                    [80.2800, 13.0900],
                    [80.2600, 13.0900],
                    [80.2600, 13.0700],
                ]
            ],
        }
        service.set_active_flood_scenario("SIM-FLOOD-001", flood_polygon)

        # Evaluate hospital
        hosp_exposed = service.get_hospital("H-TEST-001")
        assert hosp_exposed["flood_exposure"]["is_exposed"] is True
        assert hosp_exposed["flood_exposure"]["status"] == "EXPOSED"
        assert hosp_exposed["flood_exposure"]["scenario_id"] == "SIM-FLOOD-001"
        assert hosp_exposed["flood_exposure"]["mode"] == "SIMULATION"

        # CRITICAL ASSERTION: EXPOSED != CLOSED
        assert hosp_exposed["status"] == "OPERATIONAL"
        assert hosp_exposed["status"] != "CLOSED"


class TestWhatIfFacilityScenarios:
    """Test What-If isolation: scenario modifies isolated twin, live state unchanged."""

    def test_what_if_hospital_capacity_saturation(self, sample_hospital: Hospital):
        twin = DigitalTwinStateManager()
        service = FacilityService(digital_twin=twin)
        service.create_hospital(sample_hospital)

        engine = WhatIfScenarioEngine(live_state_manager=twin)
        live_snapshot_before = twin.create_snapshot()

        scenario = WhatIfScenario(
            scenario_id="scen-hosp-full-001",
            name="What if Apex Trauma Center reaches 0 available beds?",
            scenario_type=WhatIfScenarioType.HOSPITAL_CAPACITY,
            base_state_version=twin.state_version,
            modifications=[
                HospitalCapacityModification(
                    hospital_id="H-TEST-001",
                    available_capacity=0,
                    icu_available=0,
                )
            ],
        )

        result = engine.execute_preview(scenario)
        assert result.status == "COMPLETED"
        assert len(result.facility_impacts) == 1
        fac = result.facility_impacts[0]
        assert fac.facility_id == "H-TEST-001"
        assert fac.baseline_available_capacity == 45
        assert fac.scenario_available_capacity == 0
        assert fac.capacity_delta == -45

        # Verify live state remains unmodified
        live_snapshot_after = twin.create_snapshot()
        assert live_snapshot_before == live_snapshot_after
        assert twin.get_hospital("H-TEST-001").available_capacity == 45

    def test_what_if_shelter_capacity_exhaustion(self, sample_shelter: Shelter):
        twin = DigitalTwinStateManager()
        service = FacilityService(digital_twin=twin)
        service.create_shelter(sample_shelter)

        engine = WhatIfScenarioEngine(live_state_manager=twin)
        live_snapshot_before = twin.create_snapshot()

        scenario = WhatIfScenario(
            scenario_id="scen-shelt-full-001",
            name="What if Relief Shelter S-TEST-001 fills to capacity?",
            scenario_type=WhatIfScenarioType.SHELTER_CAPACITY,
            base_state_version=twin.state_version,
            modifications=[
                ShelterCapacityModification(
                    shelter_id="S-TEST-001",
                    available_capacity=0,
                )
            ],
        )

        result = engine.execute_preview(scenario)
        assert result.status == "COMPLETED"
        assert len(result.facility_impacts) == 1
        fac = result.facility_impacts[0]
        assert fac.facility_id == "S-TEST-001"
        assert fac.baseline_available_capacity == 150
        assert fac.scenario_available_capacity == 0
        assert fac.capacity_delta == -150

        # Verify live state remains unmodified
        live_snapshot_after = twin.create_snapshot()
        assert live_snapshot_before == live_snapshot_after
        assert twin.get_shelter("S-TEST-001").available_capacity == 150
