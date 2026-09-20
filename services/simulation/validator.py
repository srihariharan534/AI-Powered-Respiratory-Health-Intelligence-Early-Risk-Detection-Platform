"""
NEXUS What-If Simulation Engine - Validator.
Validates scenarios against authoritative baseline state before execution.
"""

from digital_twin.state.state_manager import DigitalTwinStateManager
from services.simulation.models import (
    BridgeFailureModification,
    FloodLevelModification,
    HospitalCapacityModification,
    ResourceShortageModification,
    ShelterCapacityModification,
    WhatIfScenario,
)



class ScenarioValidationError(ValueError):
    """Raised when a scenario fails pre-execution validation."""
    pass


class StateVersionConflictError(ScenarioValidationError):
    """Raised when scenario requested base version does not match live Digital Twin version."""
    pass


def validate_scenario_against_state(
    scenario: WhatIfScenario,
    state_manager: DigitalTwinStateManager,
) -> None:
    """
    Validates that a What-If scenario is structurally sound and compatible
    with the target Digital Twin state.
    Enforces:
    1. Base state version match (no silent stale execution).
    2. Entity existence for targeted modifications (bridges, hospitals, etc.).
    3. Capacity domain limits (available <= capacity).
    4. Positive quantities and required parameters.
    """
    # 1. State Version Validation
    if scenario.base_state_version != state_manager.state_version:
        raise StateVersionConflictError(
            f"State version mismatch: Scenario requested base version {scenario.base_state_version}, "
            f"but Digital Twin is currently at version {state_manager.state_version}."
        )

    # 2. Validate Modifications
    for idx, mod in enumerate(scenario.modifications):
        if isinstance(mod, BridgeFailureModification):
            bridge = state_manager.get_bridge(mod.bridge_id)
            if bridge is None:
                raise ScenarioValidationError(
                    f"Modification #{idx} references non-existent bridge '{mod.bridge_id}'"
                )

        elif isinstance(mod, HospitalCapacityModification):
            hospital = state_manager.get_hospital(mod.hospital_id)
            if hospital is None:
                raise ScenarioValidationError(
                    f"Modification #{idx} references non-existent hospital '{mod.hospital_id}'"
                )
            if mod.available_capacity > hospital.capacity:
                raise ScenarioValidationError(
                    f"Modification #{idx} hospital '{mod.hospital_id}' available capacity "
                    f"({mod.available_capacity}) exceeds total capacity ({hospital.capacity})"
                )
            if mod.icu_available is not None and mod.icu_available < 0:
                raise ScenarioValidationError(f"Modification #{idx} negative ICU capacity not allowed")

        elif isinstance(mod, ShelterCapacityModification):
            shelter = state_manager.get_shelter(mod.shelter_id)
            if shelter is None:
                raise ScenarioValidationError(
                    f"Modification #{idx} references non-existent shelter '{mod.shelter_id}'"
                )
            if mod.available_capacity > shelter.capacity:
                raise ScenarioValidationError(
                    f"Modification #{idx} shelter '{mod.shelter_id}' available capacity "
                    f"({mod.available_capacity}) exceeds total capacity ({shelter.capacity})"
                )

        elif isinstance(mod, FloodLevelModification):
            has_delta = mod.water_level_delta_meters is not None
            has_abs = mod.absolute_water_level_meters is not None
            has_poly = mod.flood_polygon is not None
            if not (has_delta or has_abs or has_poly):
                raise ScenarioValidationError(
                    f"Modification #{idx} flood scenario requires water_level_delta_meters, "
                    f"absolute_water_level_meters, or flood_polygon"
                )

        elif isinstance(mod, ResourceShortageModification):
            if mod.available_quantity < 0:
                raise ScenarioValidationError(f"Modification #{idx} resource quantity cannot be negative")

        else:
            raise ScenarioValidationError(f"Modification #{idx} has unsupported type: {type(mod)}")

