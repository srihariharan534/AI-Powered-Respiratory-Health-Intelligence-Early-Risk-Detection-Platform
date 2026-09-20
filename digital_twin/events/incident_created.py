"""
NEXUS Digital Twin - Incident Created and Incident Status Events.
Domain events for tracking emergency incidents within the operational state.
"""

from typing import Any, Dict, Optional

from pydantic import Field

from digital_twin.events.base import TwinEvent
from services.api.app.schemas.incident import IncidentSeverity, IncidentStatus


class IncidentCreatedEvent(TwinEvent):
    """
    Emitted when a new verified or unverified incident is ingested into the Digital Twin.
    """
    event_type: str = Field(default="INCIDENT_CREATED")
    incident_id: str = Field(..., description="Unique incident identifier")
    incident_type: str = Field(..., description="Incident category (e.g. FLOOD_STRANDED, MEDICAL_EMERGENCY)")
    severity: IncidentSeverity = Field(..., description="Incident severity level")
    status: IncidentStatus = Field(default=IncidentStatus.OPEN, description="Initial operational status")
    location: Dict[str, Any] = Field(..., description="GeoJSON geometry or coordinate mapping")
    reported_by: Optional[str] = Field(None, description="Reporting officer or source entity")
    description: Optional[str] = Field(None, description="Situational summary")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Provenance evidence link")
    priority: Optional[int] = Field(None, description="Calculated or assigned operational priority", ge=1)


class IncidentStatusChangedEvent(TwinEvent):
    """
    Emitted when an existing incident changes operational status (e.g., OPEN -> IN_PROGRESS -> RESOLVED).
    """
    event_type: str = Field(default="INCIDENT_STATUS_CHANGED")
    incident_id: str = Field(..., description="Target incident identifier")
    previous_status: Optional[IncidentStatus] = Field(None, description="Previous status")
    new_status: IncidentStatus = Field(..., description="Updated operational status")
    assigned_team_id: Optional[str] = Field(None, description="Assigned rescue team unit, if applicable")
