"""
NEXUS Flood Simulation - Severity Thresholds.
Configurable scenario-based flood severity classification.
"""

from enum import Enum

from pydantic import BaseModel, Field


class FloodSeverity(str, Enum):
    """
    Flood severity categories for scenario classification.
    Explicitly labeled as NEXUS scenario thresholds, not official emergency standards.
    """
    LOW = "LOW"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    EXTREME = "EXTREME"


class SeverityThresholds(BaseModel):
    """
    Configurable thresholds (in meters) for depth classification.
    Default NEXUS scenario thresholds:
      0.0 to low_max:       LOW       (e.g., 0.0 - 0.3m: passable by high-clearance)
      low_max to med_max:   MODERATE  (e.g., 0.3 - 1.0m: impassable to standard vehicles)
      med_max to high_max:  SEVERE    (e.g., 1.0 - 2.0m: structural threat / ground floor inundation)
      > high_max:           EXTREME   (e.g., > 2.0m: multi-story threat / life-threatening)
    """
    low_max: float = Field(default=0.3, ge=0.0, description="Upper bound for LOW severity (exclusive)")
    moderate_max: float = Field(default=1.0, ge=0.0, description="Upper bound for MODERATE severity (exclusive)")
    severe_max: float = Field(default=2.0, ge=0.0, description="Upper bound for SEVERE severity (exclusive)")

    model_config = {
        "frozen": True,
    }


DEFAULT_THRESHOLDS = SeverityThresholds()


def classify_flood_depth(
    depth_meters: float,
    thresholds: SeverityThresholds = DEFAULT_THRESHOLDS,
) -> FloodSeverity:
    """
    Deterministic classification of water depth into a FloodSeverity category.
    Enforces non-negative depth.
    Boundary semantics:
      [0.0, low_max]       -> LOW
      (low_max, mod_max]   -> MODERATE
      (mod_max, sev_max]   -> SEVERE
      > sev_max            -> EXTREME
    """
    if depth_meters < 0.0:
        raise ValueError(f"Flood depth cannot be negative: {depth_meters}m")

    if depth_meters <= thresholds.low_max:
        return FloodSeverity.LOW
    elif depth_meters <= thresholds.moderate_max:
        return FloodSeverity.MODERATE
    elif depth_meters <= thresholds.severe_max:
        return FloodSeverity.SEVERE
    else:
        return FloodSeverity.EXTREME
