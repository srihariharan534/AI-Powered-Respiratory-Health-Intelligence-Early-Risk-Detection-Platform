"""
NEXUS What-If Scenario Engine.
Authoritative counterfactual simulation and impact analysis layer.
"""

from services.simulation.executor import WhatIfScenarioEngine
from services.simulation.impact import (
    CausalStep,
    CounterfactualExplanation,
    FacilityImpactDelta,
    FloodImpactDelta,
    ResourceImpactDelta,
    RoadImpactDelta,
    RouteImpactDelta,
    WhatIfScenarioResult,
)
from services.simulation.models import (
    BaseModification,
    BridgeFailureModification,
    FloodLevelModification,
    HospitalCapacityModification,
    ResourceShortageModification,
    ScenarioLifecycleStatus,
    ScenarioModification,
    ShelterCapacityModification,
    WhatIfScenario,
    WhatIfScenarioType,
)
from services.simulation.validator import (
    ScenarioValidationError,
    StateVersionConflictError,
    validate_scenario_against_state,
)

__all__ = [
    "WhatIfScenario",
    "WhatIfScenarioType",
    "ScenarioLifecycleStatus",
    "BaseModification",
    "FloodLevelModification",
    "BridgeFailureModification",
    "HospitalCapacityModification",
    "ShelterCapacityModification",
    "ResourceShortageModification",
    "ScenarioModification",

    "ScenarioValidationError",
    "StateVersionConflictError",
    "validate_scenario_against_state",
    "WhatIfScenarioResult",
    "FloodImpactDelta",
    "RoadImpactDelta",
    "RouteImpactDelta",
    "FacilityImpactDelta",
    "ResourceImpactDelta",
    "CounterfactualExplanation",
    "CausalStep",
    "WhatIfScenarioEngine",
]
