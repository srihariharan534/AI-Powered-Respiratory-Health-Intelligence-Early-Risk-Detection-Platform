import pytest
from datetime import datetime, timezone

from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.repositories.incident_service import (
    IncidentNotFoundError,
    IncidentService,
    StateVersionConflictError,
)
from services.api.app.schemas.incident import (
    Incident,
    IncidentEventType,
    IncidentEvidence,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
    PointLocation,
)
from services.api.app.schemas.incident_lifecycle import (
    InvalidIncidentTransitionError,
    validate_incident_transition,
)


@pytest.fixture
def sample_incident() -> Incident:
    return Incident(
        schema_version="1.0.0",
        incident_id="INC-TEST-001",
        event_type=IncidentEventType.FLOOD_INUNDATION,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        priority=2,
        location=PointLocation(type="Point", coordinates=[80.27, 13.08]),
        description="Water depth reaching 70cm near intersection.",
        reported_at=datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc),
        reported_by="FIELD_OFFICER_12",
        source=IncidentSource.FIELD_OFFICER,
        evidence=IncidentEvidence(water_depth_cm=70.0, trapped_count=4),
    )


class TestIncidentLifecycleStateMachine:
    def test_valid_forward_transitions(self):
        # OPEN -> ACKNOWLEDGED
        assert validate_incident_transition(IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED) is True
        # ACKNOWLEDGED -> IN_PROGRESS
        assert validate_incident_transition(IncidentStatus.ACKNOWLEDGED, IncidentStatus.IN_PROGRESS) is True
        # IN_PROGRESS -> RESOLVED
        assert validate_incident_transition(IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED) is True

    def test_valid_cancellations(self):
        assert validate_incident_transition(IncidentStatus.OPEN, IncidentStatus.CANCELLED) is True
        assert validate_incident_transition(IncidentStatus.ACKNOWLEDGED, IncidentStatus.CANCELLED) is True
        assert validate_incident_transition(IncidentStatus.IN_PROGRESS, IncidentStatus.CANCELLED) is True

    def test_invalid_transitions_raise(self):
        # Skipping states: OPEN -> RESOLVED
        with pytest.raises(InvalidIncidentTransitionError):
            validate_incident_transition(IncidentStatus.OPEN, IncidentStatus.RESOLVED)

        # Terminal state transitions: RESOLVED -> OPEN
        with pytest.raises(InvalidIncidentTransitionError):
            validate_incident_transition(IncidentStatus.RESOLVED, IncidentStatus.OPEN)

        # Terminal state transitions: CANCELLED -> IN_PROGRESS
        with pytest.raises(InvalidIncidentTransitionError):
            validate_incident_transition(IncidentStatus.CANCELLED, IncidentStatus.IN_PROGRESS)

    def test_idempotent_same_status(self):
        assert validate_incident_transition(IncidentStatus.OPEN, IncidentStatus.OPEN) is False


class TestIncidentServiceWorkflow:
    def test_create_and_query_incident(self, sample_incident: Incident):
        dt = DigitalTwinStateManager()
        service = IncidentService(digital_twin=dt)

        record = service.create_incident(sample_incident, actor="OFFICER_42")
        assert record["incident_id"] == "INC-TEST-001"
        assert record["status"] == "OPEN"
        assert record["state_version"] == 1

        # Check Digital Twin has received the incident
        twin_incident = dt.get_incident("INC-TEST-001")
        assert twin_incident is not None
        assert twin_incident.status == IncidentStatus.OPEN

        # Check audit trail exists
        history = service.get_incident_history("INC-TEST-001")
        assert len(history) == 1
        assert history[0]["action"] == "CREATED"
        assert history[0]["actor"] == "OFFICER_42"

    def test_duplicate_incident_id_rejected(self, sample_incident: Incident):
        service = IncidentService()
        service.create_incident(sample_incident)
        with pytest.raises(ValueError, match="already exists"):
            service.create_incident(sample_incident)

    def test_end_to_end_lifecycle_progression(self, sample_incident: Incident):
        dt = DigitalTwinStateManager()
        service = IncidentService(digital_twin=dt)
        service.create_incident(sample_incident)

        # 1. Acknowledge
        rec_ack = service.update_incident_status(
            "INC-TEST-001",
            IncidentStatus.ACKNOWLEDGED,
            expected_state_version=1,
            notes="Incident acknowledged by dispatch.",
        )
        assert rec_ack["status"] == "ACKNOWLEDGED"
        assert rec_ack["state_version"] == 2
        assert dt.get_incident("INC-TEST-001").status == IncidentStatus.ACKNOWLEDGED

        # 2. In Progress
        rec_prog = service.update_incident_status(
            "INC-TEST-001",
            IncidentStatus.IN_PROGRESS,
            expected_state_version=2,
            assigned_team_id="RESCUE-03",
        )
        assert rec_prog["status"] == "IN_PROGRESS"
        assert rec_prog["state_version"] == 3
        assert rec_prog["assigned_team_id"] == "RESCUE-03"

        # 3. Resolve
        rec_res = service.update_incident_status(
            "INC-TEST-001",
            IncidentStatus.RESOLVED,
            expected_state_version=3,
            notes="Trapped citizens evacuated.",
        )
        assert rec_res["status"] == "RESOLVED"
        assert rec_res["state_version"] == 4
        assert dt.get_incident("INC-TEST-001").status == IncidentStatus.RESOLVED

        # Verify complete history
        history = service.get_incident_history("INC-TEST-001")
        assert len(history) == 4
        assert [h["state_version"] for h in history] == [1, 2, 3, 4]

    def test_optimistic_concurrency_conflict(self, sample_incident: Incident):
        service = IncidentService()
        service.create_incident(sample_incident)

        # Transition to ACKNOWLEDGED (bumps version to 2)
        service.update_incident_status("INC-TEST-001", IncidentStatus.ACKNOWLEDGED, expected_state_version=1)

        # Another coordinator tries to update based on stale version 1
        with pytest.raises(StateVersionConflictError) as exc_info:
            service.update_incident_status("INC-TEST-001", IncidentStatus.IN_PROGRESS, expected_state_version=1)

        assert exc_info.value.expected_version == 1
        assert exc_info.value.current_version == 2

    def test_update_mutable_details(self, sample_incident: Incident):
        service = IncidentService()
        service.create_incident(sample_incident)

        updated = service.update_incident_details(
            "INC-TEST-001",
            severity=IncidentSeverity.CRITICAL,
            priority=1,
            description="Water depth increased to 120cm.",
            expected_state_version=1,
        )
        assert updated["severity"] == "CRITICAL"
        assert updated["priority"] == 1
        assert updated["state_version"] == 2

    def test_list_and_filtering(self, sample_incident: Incident):
        service = IncidentService()
        service.create_incident(sample_incident)

        # Filter by severity
        highs = service.list_incidents(severity=IncidentSeverity.HIGH)
        assert highs["total"] == 1

        lows = service.list_incidents(severity=IncidentSeverity.LOW)
        assert lows["total"] == 0
