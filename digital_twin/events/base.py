"""
NEXUS Digital Twin - Base Event Model.
Foundational schema for domain events that cause state transitions in the Digital Twin.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventSource(str, Enum):
    """Authoritative source producing the operational event."""
    FIELD_REPORT = "FIELD_REPORT"
    COMMAND_CENTER = "COMMAND_CENTER"
    SIMULATION = "SIMULATION"
    SYSTEM = "SYSTEM"
    IMPORT = "IMPORT"
    TEST_FIXTURE = "TEST_FIXTURE"


class TwinEvent(BaseModel):
    """
    Abstract base event for all Digital Twin operational state changes.
    Immutable representation of an event that occurred.
    """
    event_id: str = Field(..., description="Unique deterministic event identifier for idempotency (e.g. 'EVT-001')")
    event_type: str = Field(..., description="Descriptive event type string")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware UTC timestamp when the event occurred"
    )
    source: EventSource = Field(default=EventSource.SYSTEM, description="Provenance source of the event")
    reason: Optional[str] = Field(None, description="Human or system reason/justification for the transition")
    caused_by_event_id: Optional[str] = Field(None, description="Event ID that causally triggered this event, if applicable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or payload metadata")

    model_config = {
        "frozen": True,  # Events are immutable once created
    }
