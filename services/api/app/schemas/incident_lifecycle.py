"""
NEXUS Incident Lifecycle State Machine.
Defines valid lifecycle transitions and strict validation rules.
"""

from typing import Dict, Set

from services.api.app.schemas.incident import IncidentStatus


class InvalidIncidentTransitionError(ValueError):
    """Raised when an illegal status transition is attempted on an incident."""
    pass


# Single source of truth for valid status transitions
VALID_INCIDENT_TRANSITIONS: Dict[IncidentStatus, Set[IncidentStatus]] = {
    IncidentStatus.OPEN: {
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.CANCELLED,
    },
    IncidentStatus.ACKNOWLEDGED: {
        IncidentStatus.IN_PROGRESS,
        IncidentStatus.CANCELLED,
    },
    IncidentStatus.IN_PROGRESS: {
        IncidentStatus.RESOLVED,
        IncidentStatus.CANCELLED,
    },
    IncidentStatus.RESOLVED: set(),   # Terminal state
    IncidentStatus.CANCELLED: set(),  # Terminal state
}


def validate_incident_transition(
    current_status: IncidentStatus,
    new_status: IncidentStatus,
) -> bool:
    """
    Validates whether transitioning from current_status to new_status is permitted.
    If current_status == new_status, returns False (no-op, idempotent).
    If valid, returns True.
    If illegal, raises InvalidIncidentTransitionError.
    """
    if current_status == new_status:
        return False

    allowed_targets = VALID_INCIDENT_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_targets:
        allowed_names = [s.value for s in allowed_targets]
        raise InvalidIncidentTransitionError(
            f"Cannot transition incident from '{current_status.value}' to '{new_status.value}'. "
            f"Allowed transitions from '{current_status.value}': {allowed_names or 'None (Terminal state)'}."
        )

    return True


def get_allowed_transitions(current_status: IncidentStatus) -> list[IncidentStatus]:
    """Returns a list of allowed target statuses from the current status."""
    return sorted(list(VALID_INCIDENT_TRANSITIONS.get(current_status, set())), key=lambda s: s.value)
