"""
Central Hazard Plugin Registry (Multi-Emergency Platform).
Coordinates access to all 12 emergency modules across the single Digital Twin and API.
"""

from typing import Dict, List, Optional
from services.hazards.contracts import EmergencyType, HazardModule, ModuleMaturity
from services.hazards.modules import (
    CycloneHazardModule,
    EarthquakeHazardModule,
    ExtremeHeatHazardModule,
    FloodHazardModule,
    GenericArchitectureReadyHazardModule,
    LandslideHazardModule,
    WildfireHazardModule,
)


class HazardRegistry:
    def __init__(self) -> None:
        self._modules: Dict[EmergencyType, HazardModule] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        # Deeply validated & implemented modules
        self._modules[EmergencyType.FLOOD] = FloodHazardModule()
        self._modules[EmergencyType.CYCLONE] = CycloneHazardModule()
        self._modules[EmergencyType.LANDSLIDE] = LandslideHazardModule()
        self._modules[EmergencyType.WILDFIRE] = WildfireHazardModule()
        self._modules[EmergencyType.EXTREME_HEAT] = ExtremeHeatHazardModule()
        self._modules[EmergencyType.EARTHQUAKE] = EarthquakeHazardModule()

        # Architecture-ready modules
        for etype in [
            EmergencyType.TORNADO,
            EmergencyType.SEVERE_STORM,
            EmergencyType.INDUSTRIAL_ACCIDENT,
            EmergencyType.CHEMICAL_INCIDENT,
            EmergencyType.URBAN_INFRASTRUCTURE_FAILURE,
            EmergencyType.PUBLIC_HEALTH_EMERGENCY,
            EmergencyType.MAJOR_TRANSPORT_INCIDENT,
        ]:
            self._modules[etype] = GenericArchitectureReadyHazardModule(etype)

    def get_module(self, emergency_type: EmergencyType) -> HazardModule:
        return self._modules[emergency_type]

    def list_supported_emergencies(self) -> List[Dict[str, str]]:
        return [
            {
                "emergency_type": etype.value,
                "maturity": mod.get_maturity().value,
            }
            for etype, mod in self._modules.items()
        ]
