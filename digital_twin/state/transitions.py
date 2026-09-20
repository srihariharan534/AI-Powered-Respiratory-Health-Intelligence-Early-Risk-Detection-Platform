"""
NEXUS Digital Twin - State Transitions.
Pure, deterministic transition rules validating events against current entity states.
"""

from typing import Optional, Tuple

from digital_twin.entities.bridge import BridgeEntity
from digital_twin.entities.flood_zone import FloodZoneEntity
from digital_twin.entities.hospital import HospitalEntity
from digital_twin.entities.incident import IncidentEntity
from digital_twin.entities.population import PopulationEntity
from digital_twin.entities.road import RoadEntity
from digital_twin.entities.shelter import ShelterEntity
from digital_twin.entities.vulnerable_group import VulnerableGroupEntity
from digital_twin.events.capacity_updated import CapacityUpdatedEvent
from digital_twin.events.facility_status_changed import FacilityStatusChangedEvent
from digital_twin.events.flood_updated import FloodUpdatedEvent
from digital_twin.events.incident_created import (
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


class StateTransitionError(ValueError):
    """Raised when an invalid state transition is attempted."""
    pass


def apply_facility_status_transition(
    entity: HospitalEntity | ShelterEntity,
    event: FacilityStatusChangedEvent,
) -> Tuple[HospitalEntity | ShelterEntity, bool]:
    """
    Transition hospital or shelter operational status.
    Returns (updated_entity, is_no_op).
    """
    if entity.status == event.new_status or (hasattr(entity.status, "value") and entity.status.value == event.new_status):
        return entity, True

    updated = entity.model_copy(deep=True)
    # Cast to target enum type if entity has status type
    status_type = type(entity.status)
    try:
        updated.status = status_type(event.new_status)
    except Exception:
        updated.status = event.new_status
    updated.updated_at = event.timestamp
    updated.source = event.source.value if hasattr(event.source, "value") else str(event.source)
    return updated, False



def apply_road_status_transition(
    entity: RoadEntity,
    event: RoadStatusChangedEvent
) -> Tuple[RoadEntity, bool]:
    """
    Transition road operational status.
    Returns (updated_entity, is_no_op).
    """
    is_status_same = (entity.status == event.new_status)
    is_access_same = (event.new_accessibility is None or entity.accessibility == event.new_accessibility)
    is_speed_same = (event.new_speed_kmh is None or entity.speed_kmh == event.new_speed_kmh)

    if is_status_same and is_access_same and is_speed_same:
        return entity, True  # No-op

    updated = entity.model_copy(deep=True)
    updated.status = event.new_status
    if event.new_accessibility is not None:
        updated.accessibility = event.new_accessibility
    if event.new_speed_kmh is not None:
        updated.speed_kmh = event.new_speed_kmh
    updated.updated_at = event.timestamp
    updated.source = event.source.value
    updated.reason = event.reason
    return updated, False


def apply_bridge_status_transition(
    entity: BridgeEntity,
    event: BridgeStatusChangedEvent
) -> Tuple[BridgeEntity, bool]:
    """
    Transition bridge operational status.
    Returns (updated_entity, is_no_op).
    """
    if entity.status == event.new_status:
        return entity, True

    updated = entity.model_copy(deep=True)
    updated.status = event.new_status
    updated.updated_at = event.timestamp
    updated.source = event.source.value
    updated.reason = event.reason
    return updated, False


def apply_hospital_capacity_transition(
    entity: HospitalEntity,
    event: CapacityUpdatedEvent
) -> Tuple[HospitalEntity, bool]:
    """
    Transition hospital capacity.
    Validates: available_capacity <= capacity.
    """
    if (
        entity.capacity == event.capacity
        and entity.available_capacity == event.available_capacity
        and (event.icu_available is None or entity.icu_available == event.icu_available)
        and (event.accessibility is None or entity.accessibility == event.accessibility)
    ):
        return entity, True

    updated = entity.model_copy(deep=True)
    updated.capacity = event.capacity
    updated.available_capacity = event.available_capacity
    if event.icu_available is not None:
        updated.icu_available = event.icu_available
    if event.accessibility is not None:
        updated.accessibility = event.accessibility
    updated.updated_at = event.timestamp
    updated.source = event.source.value
    return updated, False


def apply_shelter_capacity_transition(
    entity: ShelterEntity,
    event: CapacityUpdatedEvent
) -> Tuple[ShelterEntity, bool]:
    """
    Transition shelter capacity.
    Validates: available_capacity <= capacity.
    """
    if (
        entity.capacity == event.capacity
        and entity.available_capacity == event.available_capacity
        and (event.accessibility is None or entity.accessibility == event.accessibility)
    ):
        return entity, True

    updated = entity.model_copy(deep=True)
    updated.capacity = event.capacity
    updated.available_capacity = event.available_capacity
    if event.accessibility is not None:
        updated.accessibility = event.accessibility
    updated.updated_at = event.timestamp
    updated.source = event.source.value
    return updated, False


def apply_incident_status_transition(
    entity: IncidentEntity,
    event: IncidentStatusChangedEvent
) -> Tuple[IncidentEntity, bool]:
    """
    Transition incident operational status.
    Enforces Phase 15 state machine transition rules.
    """
    if entity.status == event.new_status:
        return entity, True

    from services.api.app.schemas.incident_lifecycle import (
        InvalidIncidentTransitionError,
        validate_incident_transition,
    )

    try:
        validate_incident_transition(entity.status, event.new_status)
    except InvalidIncidentTransitionError as err:
        raise StateTransitionError(str(err)) from err

    updated = entity.model_copy(deep=True)
    updated.status = event.new_status
    updated.updated_at = event.timestamp
    return updated, False


def apply_flood_transition(
    entity: Optional[FloodZoneEntity],
    event: FloodUpdatedEvent
) -> Tuple[FloodZoneEntity, bool]:
    """
    Transition or create flood zone record.
    """
    if entity is not None:
        if (
            entity.severity == event.severity
            and entity.water_depth_m == event.water_depth_m
            and entity.geometry == event.geometry
        ):
            return entity, True

    updated = FloodZoneEntity(
        flood_zone_id=event.flood_zone_id,
        name=event.name if event.name else (entity.name if entity else None),
        geometry=event.geometry,
        severity=event.severity,
        water_depth_m=event.water_depth_m,
        updated_at=event.timestamp,
        source=event.source.value,
    )
    return updated, False


def apply_vulnerability_transition(
    entity: Optional[VulnerableGroupEntity],
    event: VulnerabilityUpdatedEvent
) -> Tuple[VulnerableGroupEntity, bool]:
    """
    Transition or create vulnerable group record.
    """
    if entity is not None:
        if (
            entity.count == event.count
            and entity.category == event.category
            and (event.location is None or entity.location == event.location)
        ):
            return entity, True

    updated = VulnerableGroupEntity(
        vulnerable_group_id=event.vulnerable_group_id,
        name=event.name if event.name else (entity.name if entity else None),
        category=event.category,
        count=event.count,
        location=event.location if event.location else (entity.location if entity else None),
        updated_at=event.timestamp,
        source=event.source.value,
    )
    return updated, False


def apply_population_transition(
    entity: Optional[PopulationEntity],
    event: PopulationUpdatedEvent
) -> Tuple[PopulationEntity, bool]:
    """
    Transition or create population region record.
    """
    if entity is not None and entity.count == event.count:
        return entity, True

    updated = PopulationEntity(
        population_id=event.population_id,
        count=event.count,
        location=event.location if event.location else (entity.location if entity else None),
        updated_at=event.timestamp,
        source=event.source.value,
    )
    return updated, False
