"""
NEXUS What-If Simulation Engine - Scenario Models.
Defines hypothetical modifications, lifecycle states, and scenario definitions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ScenarioLifecycleStatus(str, Enum):
    """Lifecycle progression states for a What-If scenario."""
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WhatIfScenarioType(str, Enum):
    """Supported scenario modification families."""
    FLOOD_LEVEL = "flood_level"
    BRIDGE_FAILURE = "bridge_failure"
    HOSPITAL_CAPACITY = "hospital_capacity"
    SHELTER_CAPACITY = "shelter_capacity"
    RESOURCE_SHORTAGE = "resource_shortage"
    COMPOUND = "compound"  # Multi-modification scenario


class BaseModification(BaseModel):
    """Abstract base model for scenario modifications."""
    type: WhatIfScenarioType = Field(..., description="Type identifier for this modification")
    description: Optional[str] = Field(None, description="Human-readable description of modification")

    model_config = {
        "frozen": True,
    }


class FloodLevelModification(BaseModification):
    """Hypothetical flood level increase or explicit extent scenario."""
    type: WhatIfScenarioType = Field(default=WhatIfScenarioType.FLOOD_LEVEL)
    water_level_delta_meters: Optional[float] = Field(None, ge=0.0, description="Increment above baseline (e.g. +1.0m)")
    absolute_water_level_meters: Optional[float] = Field(None, description="Absolute flood water level in meters")
    flood_polygon: Optional[Dict[str, Any]] = Field(None, description="Explicit GeoJSON flood extent polygon")
    explicit_depth_meters: Optional[float] = Field(None, ge=0.0, description="Uniform flood depth for explicit polygon")
    auto_close_roads: bool = Field(default=True, description="Whether to apply road closure thresholds in scenario")
    road_closure_threshold_meters: float = Field(default=0.3, ge=0.0, description="Closure threshold depth in meters")


class BridgeFailureModification(BaseModification):
    """Hypothetical bridge structural failure or closure."""
    type: WhatIfScenarioType = Field(default=WhatIfScenarioType.BRIDGE_FAILURE)
    bridge_id: str = Field(..., description="Identifier of bridge that fails (e.g. 'B-001')")
    propagate_to_road: bool = Field(default=True, description="Whether to causally close the associated road")


class HospitalCapacityModification(BaseModification):
    """Hypothetical hospital facility capacity reduction or saturation."""
    type: WhatIfScenarioType = Field(default=WhatIfScenarioType.HOSPITAL_CAPACITY)
    hospital_id: str = Field(..., description="Target hospital identifier (e.g. 'H-001')")
    available_capacity: int = Field(..., ge=0, description="Hypothetical available bed capacity")
    icu_available: Optional[int] = Field(None, ge=0, description="Hypothetical available ICU capacity")


class ShelterCapacityModification(BaseModification):
    """Hypothetical shelter facility capacity reduction or exhaustion."""
    type: WhatIfScenarioType = Field(default=WhatIfScenarioType.SHELTER_CAPACITY)
    shelter_id: str = Field(..., description="Target shelter identifier (e.g. 'S-001')")
    available_capacity: int = Field(..., ge=0, description="Hypothetical available shelter occupancy spots")


class ResourceShortageModification(BaseModification):
    """Hypothetical emergency unit or rescue resource reduction."""
    type: WhatIfScenarioType = Field(default=WhatIfScenarioType.RESOURCE_SHORTAGE)
    resource_type: str = Field(..., description="Type of resource (e.g., 'rescue_team', 'ambulance', 'boat')")
    available_quantity: int = Field(..., ge=0, description="Hypothetical remaining operational units")
    affected_team_ids: List[str] = Field(default_factory=list, description="Specific team IDs disabled, if known")


ScenarioModification = Union[
    FloodLevelModification,
    BridgeFailureModification,
    HospitalCapacityModification,
    ShelterCapacityModification,
    ResourceShortageModification,
]



class WhatIfScenario(BaseModel):
    """
    Formal What-If Scenario Definition.
    Always executes against a specified base_state_version of the Digital Twin.
    """
    scenario_id: str = Field(..., min_length=3, description="Unique, deterministic scenario identifier")
    name: str = Field(..., description="Human-readable scenario title")
    description: Optional[str] = Field(None, description="Detailed counterfactual question or narrative")
    scenario_type: WhatIfScenarioType = Field(..., description="Primary or compound scenario type")
    mode: str = Field(default="SIMULATION", description="Always 'SIMULATION' or 'TEST_FIXTURE'")
    base_state_version: int = Field(..., ge=0, description="Required authoritative Digital Twin version baseline")
    modifications: List[ScenarioModification] = Field(..., min_length=1, description="List of sequential modifications")
    assumptions: List[str] = Field(default_factory=list, description="Explicit modeling assumptions")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata")

    model_config = {
        "frozen": True,
    }
