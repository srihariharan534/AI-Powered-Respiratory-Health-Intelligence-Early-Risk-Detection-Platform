"""
NEXUS Digital Twin - State Package.
Canonical export of the Digital Twin state authority, manager, and snapshots.
"""

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
]
