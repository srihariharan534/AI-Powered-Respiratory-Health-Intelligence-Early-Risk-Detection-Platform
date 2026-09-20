"""
NEXUS Digital Twin.
Shared operational emergency state authority for NEXUS.
"""

from digital_twin.entities import (
    BridgeEntity,
    FloodZoneEntity,
    HospitalEntity,
    IncidentEntity,
    PopulationEntity,
    RescueTeamEntity,
    RescueTeamStatus,
    RoadEntity,
    ShelterEntity,
    VulnerabilityCategory,
    VulnerableGroupEntity,
)
from digital_twin.events import (
    BridgeStatusChangedEvent,
    CapacityUpdatedEvent,
    EventSource,
    FloodUpdatedEvent,
    IncidentCreatedEvent,
    IncidentStatusChangedEvent,
    PopulationUpdatedEvent,
    RoadStatusChangedEvent,
    TwinEvent,
    VulnerabilityUpdatedEvent,
)
from digital_twin.state.state_manager import (
    DigitalTwinStateManager,
    TransitionResult,
    TwinSnapshot,
)
from digital_twin.state.transitions import StateTransitionError

__all__ = [
    "DigitalTwinStateManager",
    "TwinSnapshot",
    "TransitionResult",
    "StateTransitionError",
    "RoadEntity",
    "BridgeEntity",
    "HospitalEntity",
    "ShelterEntity",
    "RescueTeamEntity",
    "RescueTeamStatus",
    "IncidentEntity",
    "FloodZoneEntity",
    "PopulationEntity",
    "VulnerableGroupEntity",
    "VulnerabilityCategory",
    "TwinEvent",
    "EventSource",
    "RoadStatusChangedEvent",
    "BridgeStatusChangedEvent",
    "IncidentCreatedEvent",
    "IncidentStatusChangedEvent",
    "FloodUpdatedEvent",
    "CapacityUpdatedEvent",
    "VulnerabilityUpdatedEvent",
    "PopulationUpdatedEvent",
]
