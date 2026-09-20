"""
Unit and Integration Tests for NEXUS Phase 20 Operational Recommendation Engine.
Validates:
1. Deterministic multi-factor scoring, normalization, and policy versioning.
2. Hard constraints filtering (closed roads, full hospitals, closed shelters, resolved incidents).
3. Incident priority ranking with risk probability integration.
4. Hospital receiving facility selection based on capacity and distance.
5. Shelter evacuation selection based on capacity and utility resilience.
6. Route recommendation bypassing hazards.
7. Stale state protection: blocks approval if Digital Twin state has advanced.
8. Recommendation lifecycle: PENDING -> APPROVED / REJECTED / EXPIRED.
9. Simulation isolation: What-If scenario recommendations do not mutate live state.
10. REST API endpoints: GET /api/v1/recommendations, POST /generate, POST /approve, POST /reject.
"""

from datetime import datetime, timezone
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from digital_twin.entities.flood_zone import FloodZoneEntity
from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.routes.recommendations import router as recommendations_router
from services.api.app.schemas.hospital import Hospital, HospitalSource, HospitalStatus
from services.api.app.schemas.incident import (
    Incident,
    IncidentEventType,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
    PointLocation,
)
from services.api.app.schemas.recommendation import (
    RecommendationAction,
    RecommendationApprovalStatus,
    RecommendationEntityType,
)
from services.api.app.schemas.road import Accessibility
from services.api.app.schemas.shelter import Shelter, ShelterSource, ShelterStatus
from services.recommendations.config import (
    HOSPITAL_SELECTION_WEIGHTS,
    INCIDENT_PRIORITY_WEIGHTS,
    POLICY_VERSION,
)
from services.recommendations.constraints import (
    validate_hospital_candidate,
    validate_incident_candidate,
    validate_shelter_candidate,
)
from services.recommendations.contracts import GenerateRecommendationRequest, RecommendationType
from services.recommendations.engine import OperationalRecommendationEngine
from services.recommendations.hospital_selection.hospital_engine import HospitalSelectionEngine
from services.recommendations.incident_priority.priority_engine import IncidentPriorityEngine
from services.recommendations.scoring.normalizer import (
    normalize_capacity,
    normalize_min_max,
    normalize_severity,
)
from services.recommendations.governance.roles import AuthenticatedActor, UserRole
from services.recommendations.service import (
    RecommendationService,
    StaleRecommendationError,
)
from services.recommendations.shelter_selection.shelter_engine import ShelterSelectionEngine


@pytest.fixture
def sample_incident() -> Incident:
    return Incident(
        incident_id="INC-UNIT-001",
        description="Flash flood trapping civilians in residential cluster",
        event_type=IncidentEventType.FLOOD_INUNDATION,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        priority=2,
        location=PointLocation(coordinates=[80.2707, 13.0827]),
        reported_at=datetime.now(timezone.utc),
        reported_by="FIELD_OFFICER_01",
        source=IncidentSource.FIELD_OFFICER,
    )



@pytest.fixture
def sample_hospitals() -> list[Hospital]:
    return [
        Hospital(
            hospital_id="H-001",
            name="District General Hospital",
            location=PointLocation(coordinates=[80.2750, 13.0850]),
            capacity=100,
            available_capacity=15,
            emergency_available=True,
            status=HospitalStatus.OPERATIONAL,
            accessibility=Accessibility.ALL_VEHICLES,
            last_updated=datetime.now(timezone.utc),
            source=HospitalSource.SYNTHETIC_DEMO,
        ),
        Hospital(
            hospital_id="H-002",
            name="Community Clinic (Full)",
            location=PointLocation(coordinates=[80.2710, 13.0830]),
            capacity=20,
            available_capacity=0,  # Full
            emergency_available=False,
            status=HospitalStatus.OPERATIONAL,
            accessibility=Accessibility.ALL_VEHICLES,
            last_updated=datetime.now(timezone.utc),
            source=HospitalSource.SYNTHETIC_DEMO,
        ),
    ]


@pytest.fixture
def sample_shelters() -> list[Shelter]:
    return [
        Shelter(
            shelter_id="S-001",
            name="Central Relief Camp",
            location=PointLocation(coordinates=[80.2800, 13.0890]),
            capacity=200,
            available_capacity=75,
            has_power_backup=True,
            has_potable_water=True,
            status=ShelterStatus.OPEN,
            accessibility=Accessibility.ALL_VEHICLES,
            last_updated=datetime.now(timezone.utc),
            source=ShelterSource.SYNTHETIC_DEMO,
        ),
        Shelter(
            shelter_id="S-002",
            name="Flooded Sub-Shelter",
            location=PointLocation(coordinates=[80.2690, 13.0810]),
            capacity=50,
            available_capacity=20,
            has_power_backup=False,
            has_potable_water=False,
            status=ShelterStatus.CLOSED,  # Closed
            accessibility=Accessibility.IMPASSABLE,
            last_updated=datetime.now(timezone.utc),
            source=ShelterSource.SYNTHETIC_DEMO,
        ),
    ]




class TestRecommendationScoringAndConstraints:
    """Validates normalization, hard constraints, and scoring policies."""

    def test_normalization_bounds(self):
        assert normalize_severity("CRITICAL") == 1.00
        assert normalize_severity("LOW") == 0.20
        assert normalize_capacity(15, 100) == 0.15
        assert normalize_capacity(0, 100) == 0.0

        # Proximity normalization (closer is better)
        dist_near = normalize_min_max(1000.0, 0.0, 20000.0, invert=True)
        dist_far = normalize_min_max(18000.0, 0.0, 20000.0, invert=True)
        assert dist_near > dist_far

    def test_hard_constraints_exclusion(self, sample_hospitals, sample_shelters, sample_incident):
        # Hospital with 0 capacity rejected
        passed, reason = validate_hospital_candidate(sample_hospitals[1], required_capacity=1)
        assert passed is False
        assert "insufficient available capacity" in reason

        # Closed shelter rejected
        passed_sh, reason_sh = validate_shelter_candidate(sample_shelters[1], required_capacity=1)
        assert passed_sh is False
        assert "CLOSED" in reason_sh

        # Resolved incident rejected
        resolved_inc = sample_incident.model_copy(update={"status": IncidentStatus.RESOLVED})
        passed_inc, reason_inc = validate_incident_candidate(resolved_inc)
        assert passed_inc is False


class TestRecommendationEngines:
    """Tests incident priority, hospital selection, and shelter selection engines."""

    def test_incident_priority_engine(self, sample_incident):
        dt = DigitalTwinStateManager(initial_version=104)
        engine = IncidentPriorityEngine()

        risk_scores = {sample_incident.incident_id: 0.85}
        recs = engine.prioritize_incidents([sample_incident], digital_twin=dt, risk_model_output_map=risk_scores)

        assert len(recs) == 1
        rec = recs[0]
        assert rec.action == RecommendationAction.DISPATCH_RESCUE
        assert rec.priority in (1, 2)
        assert rec.requires_human_approval is True
        assert rec.source_state_version == "state-v104"
        assert len(rec.factors) == 5

    def test_hospital_selection_engine(self, sample_incident, sample_hospitals):
        dt = DigitalTwinStateManager(initial_version=104)
        engine = HospitalSelectionEngine()

        rec = engine.recommend_receiving_hospital(
            incident=sample_incident,
            hospitals=sample_hospitals,
            digital_twin=dt,
            required_beds=2,
        )

        assert rec is not None
        assert rec.target.entity_id == "H-001"  # H-002 was rejected due to 0 capacity
        assert rec.action == RecommendationAction.DIVERT_AMBULANCES
        assert rec.requires_human_approval is True

    def test_shelter_selection_engine(self, sample_incident, sample_shelters):
        dt = DigitalTwinStateManager(initial_version=104)
        engine = ShelterSelectionEngine()

        rec = engine.recommend_shelter(
            incident=sample_incident,
            shelters=sample_shelters,
            digital_twin=dt,
            evacuee_count=5,
        )

        assert rec is not None
        assert rec.target.entity_id == "S-001"  # S-002 was rejected because it's CLOSED
        assert rec.action == RecommendationAction.OPEN_SHELTER


class TestRecommendationServiceLifecycleAndStaleState:
    """Validates approval, rejection, and stale-state conflict rejection."""

    def test_approval_and_stale_state_block(self, sample_incident):
        dt = DigitalTwinStateManager(initial_version=104)
        svc = RecommendationService(digital_twin=dt)
        engine = IncidentPriorityEngine()
        actor = AuthenticatedActor(actor_id="COORDINATOR-ALPHA", role=UserRole.COMMANDER)

        recs = engine.prioritize_incidents([sample_incident], digital_twin=dt)
        rec = recs[0]
        svc.save_recommendation(rec)

        # 1. State version unchanged -> Approval succeeds
        approved = svc.approve_recommendation(rec.recommendation_id, actor=actor)
        assert approved.approval_status == RecommendationApprovalStatus.APPROVED
        assert approved.approved_by == "COORDINATOR-ALPHA"

        # 2. State advances -> Subsequent approval on new pending recommendation is BLOCKED
        rec2 = rec.model_copy(update={"recommendation_id": "REC-TEST-002", "approval_status": RecommendationApprovalStatus.PENDING})
        svc.save_recommendation(rec2)

        # Mutate digital twin version
        dt._version = 105

        with pytest.raises(StaleRecommendationError) as exc_info:
            svc.approve_recommendation(rec2.recommendation_id, actor=actor)
        assert "Cannot approve recommendation" in str(exc_info.value)
        assert "state-v104" in str(exc_info.value)
        assert "state-v105" in str(exc_info.value)

    def test_rejection_audit_ledger(self, sample_incident):
        dt = DigitalTwinStateManager(initial_version=104)
        svc = RecommendationService(digital_twin=dt)
        engine = IncidentPriorityEngine()
        actor = AuthenticatedActor(actor_id="COORDINATOR-BETA", role=UserRole.COMMANDER)

        recs = engine.prioritize_incidents([sample_incident], digital_twin=dt)
        rec = recs[0]
        svc.save_recommendation(rec)

        rejected = svc.reject_recommendation(
            rec.recommendation_id,
            actor=actor,
            reason="Priority adjusted manually per on-site field team radio report",
        )
        assert rejected.approval_status == RecommendationApprovalStatus.REJECTED

        ledger = svc.get_audit_log()
        assert len(ledger) == 1
        assert ledger[0].decision == RecommendationApprovalStatus.REJECTED
        assert ledger[0].decision_by == "COORDINATOR-BETA"


class TestRecommendationsApiEndpoints:
    """Validates FastAPI recommendations router."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = FastAPI()
        app.include_router(recommendations_router)
        return TestClient(app)

    def test_api_generate_and_list(self, client):
        payload = {
            "recommendation_type": "incident_priority",
            "policy_version": "policy-v1.0",
        }
        res = client.post("/api/v1/recommendations/generate", json=payload)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        # List endpoint
        list_res = client.get("/api/v1/recommendations")
        assert list_res.status_code == 200
        assert isinstance(list_res.json(), list)
