"""
NEXUS Digital Twin - Events Package.
Canonical export of all domain events accepted by the Digital Twin.
"""

from digital_twin.events.base import EventSource, TwinEvent
from digital_twin.events.capacity_updated import CapacityUpdatedEvent
from digital_twin.events.facility_status_changed import FacilityStatusChangedEvent
from digital_twin.events.flood_updated import FloodUpdatedEvent
from digital_twin.events.incident_created import (
    IncidentCreatedEvent,
    IncidentStatusChangedEvent,
)
from digital_twin.events.road_status_changed import (
    BridgeStatusChangedEvent,
    RoadStatusChangedEvent,
)
from digital_twin.events.vulnerability_updated import (
    PopulationUpdatedEvent,
    VulnerabilityUpdatedEvent,
)

__all__ = [
    "TwinEvent",
    "EventSource",
    "RoadStatusChangedEvent",
    "BridgeStatusChangedEvent",
    "IncidentCreatedEvent",
    "IncidentStatusChangedEvent",
    "FloodUpdatedEvent",
    "CapacityUpdatedEvent",
    "FacilityStatusChangedEvent",
    "VulnerabilityUpdatedEvent",
    "PopulationUpdatedEvent",
]

