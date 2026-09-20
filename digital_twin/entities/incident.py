"""
NEXUS Digital Twin - Incident Entity.
Operational emergency incident state tracked within the operational twin.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from services.api.app.schemas.incident import IncidentSeverity, IncidentStatus


class IncidentEntity(BaseModel):
    """
    Operational representation of an incident in the emergency environment.
    Conforms to canonical Phase 04 incident properties.
    """
    incident_id: str = Field(..., description="Unique incident identifier (e.g. 'INC-001')")
    event_type: str = Field(..., description="Type of incident (e.g. FLOOD_STRANDED, INFRASTRUCTURE_COLLAPSE)")
    severity: IncidentSeverity = Field(..., description="Severity level: LOW, MEDIUM, HIGH, CRITICAL")
    status: IncidentStatus = Field(default=IncidentStatus.OPEN, description="Incident operational status")
    location: Dict[str, Any] = Field(..., description="Spatial coordinates or GeoJSON geometry")
    reported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of initial report")
    reported_by: Optional[str] = Field(None, description="Reporter identity or agency")
    description: Optional[str] = Field(None, description="Detailed situational description")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Associated evidence or provenance link")
    source: str = Field(default="FIELD_REPORT", description="Provenance source of incident")
    priority: Optional[int] = Field(None, description="Operational priority integer", ge=1)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last state change timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata")

    model_config = {
        "frozen": False,
        "validate_assignment": True,
    }
