"""
NEXUS Digital Twin - Entities Package.
Canonical export of all Digital Twin operational entities.
"""

from digital_twin.entities.bridge import BridgeEntity, BridgeStatus
from digital_twin.entities.flood_zone import FloodSeverity, FloodZoneEntity
from digital_twin.entities.hospital import HospitalEntity
from digital_twin.entities.incident import IncidentEntity
from digital_twin.entities.population import PopulationEntity
from digital_twin.entities.rescue_team import RescueTeamEntity, RescueTeamStatus
from digital_twin.entities.road import RoadEntity
from digital_twin.entities.shelter import ShelterEntity
from digital_twin.entities.vulnerable_group import VulnerabilityCategory, VulnerableGroupEntity

__all__ = [
    "RoadEntity",
    "BridgeEntity",
    "BridgeStatus",
    "HospitalEntity",
    "ShelterEntity",
    "RescueTeamEntity",
    "RescueTeamStatus",
    "IncidentEntity",
    "FloodZoneEntity",
    "FloodSeverity",
    "PopulationEntity",
    "VulnerableGroupEntity",
    "VulnerabilityCategory",
]
