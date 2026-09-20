"""
Incident Service and Repository.
Manages incident lifecycle transitions, optimistic concurrency validation,
audit history tracking, and Digital Twin event synchronization.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from digital_twin.events.base import EventSource
from digital_twin.events.incident_created import (
    IncidentCreatedEvent,
    IncidentStatusChangedEvent,
)
from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.schemas.incident import (
    Incident,
    IncidentEventType,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
    PointLocation,
)
from services.api.app.schemas.incident_lifecycle import (
    InvalidIncidentTransitionError,
    get_allowed_transitions,
    validate_incident_transition,
)


class IncidentAuditEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str
    action: str
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Dict[str, Any]
    state_version: int
    details: Optional[str] = None


class StateVersionConflictError(Exception):
    """Raised when an update is submitted against an outdated state version."""
    def __init__(self, incident_id: str, expected_version: int, current_version: int):
        super().__init__(
            f"State version conflict on incident {incident_id}. "
            f"Expected version: {expected_version}, current state version: {current_version}."
        )
        self.incident_id = incident_id
        self.expected_version = expected_version
        self.current_version = current_version


class IncidentNotFoundError(Exception):
    """Raised when the requested incident ID does not exist."""
    pass


class IncidentService:
    """
    In-memory and authoritative operational service for Incidents.
    Synchronizes directly with the central Digital Twin state manager.
    """

    def __init__(self, digital_twin: Optional[DigitalTwinStateManager] = None):
        self.digital_twin = digital_twin or DigitalTwinStateManager()
        # Incident in-memory store: incident_id -> Incident dict
        self._incidents: Dict[str, Dict[str, Any]] = {}
        # Audit history: incident_id -> List[IncidentAuditEntry]
        self._audit_logs: Dict[str, List[IncidentAuditEntry]] = {}

    def create_incident(
        self,
        incident_in: Incident,
        actor: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Creates a new incident:
        1. Validates ID uniqueness.
        2. Validates GeoJSON coordinates.
        3. Initializes state version at 1.
        4. Emits IncidentCreatedEvent to the Digital Twin.
        5. Records initial audit history entry.
        """
        if incident_in.incident_id in self._incidents:
            raise ValueError(f"Incident with ID '{incident_in.incident_id}' already exists.")

        # Coordinate check
        lon, lat = incident_in.location.coordinates[0], incident_in.location.coordinates[1]
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise ValueError(f"Invalid coordinates [{lon}, {lat}]. Must be within WGS84 bounds.")

        # Construct incident record
        record: Dict[str, Any] = incident_in.model_dump(mode="json")
        record["state_version"] = 1
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        record["updated_at"] = record["created_at"]

        # Map source to EventSource enum
        source_enum = EventSource.FIELD_REPORT
        if incident_in.source == IncidentSource.SIMULATOR:
            source_enum = EventSource.SIMULATION
        elif incident_in.source == IncidentSource.SYNTHETIC_DEMO:
            source_enum = EventSource.TEST_FIXTURE
        elif incident_in.source == IncidentSource.MANUAL_ENTRY:
            source_enum = EventSource.COMMAND_CENTER

        # Emit to Digital Twin
        dt_event = IncidentCreatedEvent(
            event_id=f"EVT-CREATE-{incident_in.incident_id}",
            timestamp=datetime.now(timezone.utc),
            source=source_enum,
            incident_id=incident_in.incident_id,
            incident_type=incident_in.event_type.value,
            severity=incident_in.severity,
            status=incident_in.status,
            location=incident_in.location.model_dump(),
            reported_by=incident_in.reported_by,
            description=incident_in.description,
            evidence=incident_in.evidence.model_dump() if incident_in.evidence else None,
            priority=incident_in.priority,
        )
        self.digital_twin.apply_event(dt_event)

        # Record in local store and audit trail
        self._incidents[incident_in.incident_id] = record
        self._audit_logs[incident_in.incident_id] = [
            IncidentAuditEntry(
                actor=actor,
                action="CREATED",
                previous_state=None,
                new_state=record,
                state_version=1,
                details=f"Incident {incident_in.incident_id} created with status {incident_in.status.value}",
            )
        ]

        return record

    def get_incident(self, incident_id: str) -> Dict[str, Any]:
        """Retrieve an incident by its ID."""
        if incident_id not in self._incidents:
            raise IncidentNotFoundError(f"Incident '{incident_id}' not found.")
        record = dict(self._incidents[incident_id])
        current_status = IncidentStatus(record["status"])
        record["allowed_transitions"] = [s.value for s in get_allowed_transitions(current_status)]
        return record

    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        event_type: Optional[IncidentEventType] = None,
        source: Optional[IncidentSource] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List incidents with filtering and pagination."""
        items = list(self._incidents.values())

        if status:
            items = [i for i in items if i["status"] == status.value]
        if severity:
            items = [i for i in items if i["severity"] == severity.value]
        if event_type:
            items = [i for i in items if i["event_type"] == event_type.value]
        if source:
            items = [i for i in items if i["source"] == source.value]

        # Deterministic sort by reported_at descending
        items.sort(key=lambda x: str(x.get("reported_at", "")), reverse=True)

        total_count = len(items)
        paginated_items = items[offset : offset + limit]

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "items": paginated_items,
        }

    def update_incident_status(
        self,
        incident_id: str,
        new_status: IncidentStatus,
        expected_state_version: Optional[int] = None,
        actor: str = "COORDINATOR",
        notes: Optional[str] = None,
        assigned_team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transitions incident status:
        1. Validates transition using the state machine.
        2. Validates optimistic concurrency version.
        3. Emits IncidentStatusChangedEvent to Digital Twin.
        4. Increments state version and appends audit entry.
        """
        record = self.get_incident(incident_id)
        current_status = IncidentStatus(record["status"])
        current_version = record["state_version"]

        # Optimistic Concurrency check
        if expected_state_version is not None and expected_state_version != current_version:
            raise StateVersionConflictError(incident_id, expected_state_version, current_version)

        # Validate Lifecycle State Transition
        validate_incident_transition(current_status, new_status)

        # Update record
        previous_state = dict(record)
        record["status"] = new_status.value
        record["state_version"] = current_version + 1
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        if assigned_team_id:
            record["assigned_team_id"] = assigned_team_id

        # Digital Twin event
        dt_event = IncidentStatusChangedEvent(
            event_id=f"EVT-STATUS-{incident_id}-v{record['state_version']}",
            timestamp=datetime.now(timezone.utc),
            source=EventSource.COMMAND_CENTER,
            incident_id=incident_id,
            previous_status=current_status,
            new_status=new_status,
            assigned_team_id=assigned_team_id,
        )
        self.digital_twin.apply_event(dt_event)

        # Record audit history
        self._incidents[incident_id] = record
        self._audit_logs[incident_id].append(
            IncidentAuditEntry(
                actor=actor,
                action=f"STATUS_TRANSITION_{new_status.value}",
                previous_state=previous_state,
                new_state=record,
                state_version=record["state_version"],
                details=notes or f"Status transitioned from {current_status.value} to {new_status.value}",
            )
        )

        return self.get_incident(incident_id)

    def update_incident_details(
        self,
        incident_id: str,
        severity: Optional[IncidentSeverity] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        expected_state_version: Optional[int] = None,
        actor: str = "COORDINATOR",
    ) -> Dict[str, Any]:
        """
        Updates mutable fields of an incident with optimistic concurrency check.
        """
        record = self.get_incident(incident_id)
        current_version = record["state_version"]

        if expected_state_version is not None and expected_state_version != current_version:
            raise StateVersionConflictError(incident_id, expected_state_version, current_version)

        previous_state = dict(record)
        has_changed = False

        if severity is not None and record["severity"] != severity.value:
            record["severity"] = severity.value
            has_changed = True

        if description is not None and record["description"] != description:
            record["description"] = description
            has_changed = True

        if priority is not None and record["priority"] != priority:
            record["priority"] = priority
            has_changed = True

        if has_changed:
            record["state_version"] = current_version + 1
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._incidents[incident_id] = record
            self._audit_logs[incident_id].append(
                IncidentAuditEntry(
                    actor=actor,
                    action="DETAILS_UPDATED",
                    previous_state=previous_state,
                    new_state=record,
                    state_version=record["state_version"],
                    details="Incident mutable attributes updated",
                )
            )

        return self.get_incident(incident_id)

    def get_incident_history(self, incident_id: str) -> List[Dict[str, Any]]:
        """Retrieve the chronological audit history for an incident."""
        if incident_id not in self._incidents:
            raise IncidentNotFoundError(f"Incident '{incident_id}' not found.")
        return [entry.model_dump(mode="json") for entry in self._audit_logs.get(incident_id, [])]
