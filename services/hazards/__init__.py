"""
Hazard Package Exports (Multi-Emergency Platform).
"""

from services.hazards.contracts import (
    EmergencyEvent,
    EmergencySeverity,
    EmergencyStatus,
    EmergencyType,
    HazardModule,
    HazardRiskResult,
    ModuleMaturity,
)
from services.hazards.registry import HazardRegistry

__all__ = [
    "EmergencyType",
    "EmergencySeverity",
    "EmergencyStatus",
    "ModuleMaturity",
    "EmergencyEvent",
    "HazardRiskResult",
    "HazardModule",
    "HazardRegistry",
]
