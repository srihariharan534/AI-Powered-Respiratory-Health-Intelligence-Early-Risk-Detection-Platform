"""
Facility Service and Repository.
Authoritative operational management for Hospitals and Shelters in NEXUS.
Coordinates:
- Canonical schema validation
- Capacity & status validation
- Digital Twin State Authority synchronization
- State versioning & optimistic concurrency checks
- Chronological immutable audit trail
- Flood exposure intersection testing (without automated closure)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from shapely.geometry import Point, shape

from digital_twin.entities.hospital import HospitalEntity
from digital_twin.entities.shelter import ShelterEntity
from digital_twin.events.base import EventSource
from digital_twin.events.capacity_updated import CapacityUpdatedEvent
from digital_twin.events.facility_status_changed import FacilityStatusChangedEvent
from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.schemas.hospital import (
    Hospital,
    HospitalSource,
    HospitalStatus,
)
from services.api.app.schemas.road import Accessibility
from services.api.app.schemas.shelter import (
    Shelter,
    ShelterSource,
    ShelterStatus,
)


class FacilityAuditEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str
    action: str
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Dict[str, Any]
    state_version: int
    details: Optional[str] = None


class FacilityNotFoundError(Exception):
    """Raised when the requested hospital or shelter ID does not exist."""
    pass


class FacilityStateVersionConflictError(Exception):
    """Raised when an update is submitted against an outdated state version."""
    def __init__(self, facility_id: str, expected_version: int, current_version: int):
        super().__init__(
            f"State version conflict on facility '{facility_id}'. "
            f"Expected version {expected_version}, but current version is {current_version}."
        )
        self.facility_id = facility_id
        self.expected_version = expected_version
        self.current_version = current_version


class FacilityService:
    """
    Operational service and repository for Hospitals and Shelters.
    Synchronizes directly with the central DigitalTwinStateManager.
    """

    def __init__(self, digital_twin: Optional[DigitalTwinStateManager] = None):
        self.digital_twin = digital_twin or DigitalTwinStateManager()
        # Storage: hospital_id -> dict
        self._hospitals: Dict[str, Dict[str, Any]] = {}
        # Storage: shelter_id -> dict
        self._shelters: Dict[str, Dict[str, Any]] = {}
        # Audit history: facility_id -> List[FacilityAuditEntry]
        self._audit_logs: Dict[str, List[FacilityAuditEntry]] = {}
        # Active flood polygon GeoJSON (for flood exposure testing)
        self._active_flood_polygon: Optional[Dict[str, Any]] = None
        self._active_flood_scenario_id: Optional[str] = None

    def set_active_flood_scenario(
        self,
        scenario_id: Optional[str],
        polygon_geojson: Optional[Dict[str, Any]],
    ) -> None:
        """Sets the active simulated flood polygon for spatial exposure evaluation."""
        self._active_flood_scenario_id = scenario_id
        self._active_flood_polygon = polygon_geojson

    def evaluate_flood_exposure(self, location_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates whether a WGS84 point intersects the active flood polygon.
        Critical Rule: EXPOSED != CLOSED. Does NOT mutate facility status.
        """
        if not self._active_flood_polygon:
            return {
                "is_exposed": False,
                "status": "NOT_EVALUATED",
                "scenario_id": None,
                "mode": None,
                "evaluated": False,
            }

        try:
            poly_geom = shape(self._active_flood_polygon)
            coords = location_dict.get("coordinates", [0.0, 0.0])
            pt = Point(coords[0], coords[1])  # [lon, lat]
            intersects = bool(poly_geom.intersects(pt))

            return {
                "is_exposed": intersects,
                "status": "EXPOSED" if intersects else "CLEAR",
                "scenario_id": self._active_flood_scenario_id or "SIMULATED-FLOOD-CURRENT",
                "mode": "SIMULATION",
                "evaluated": True,
            }
        except Exception:
            return {
                "is_exposed": False,
                "status": "EVALUATION_ERROR",
                "scenario_id": self._active_flood_scenario_id,
                "mode": "SIMULATION",
                "evaluated": False,
            }

    # =========================================================================
    # HOSPITAL OPERATIONS
    # =========================================================================

    def create_hospital(
        self,
        hospital_in: Hospital,
        actor: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Creates a new operational hospital entity.
        Validates WGS84 coordinates, bounds (0 <= available <= capacity),
        registers in Digital Twin, and appends audit trail.
        """
        if hospital_in.hospital_id in self._hospitals:
            raise ValueError(f"Hospital with ID '{hospital_in.hospital_id}' already exists.")

        lon, lat = hospital_in.location.coordinates[0], hospital_in.location.coordinates[1]
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise ValueError(f"Invalid coordinates [{lon}, {lat}]. Must be within WGS84 bounds.")

        if hospital_in.available_capacity > hospital_in.capacity:
            raise ValueError(
                f"available_capacity ({hospital_in.available_capacity}) cannot exceed total capacity ({hospital_in.capacity})."
            )

        record: Dict[str, Any] = hospital_in.model_dump(mode="json")
        record["state_version"] = 1
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        record["last_updated"] = record["created_at"]

        # Register with Digital Twin
        twin_entity = HospitalEntity(
            hospital_id=hospital_in.hospital_id,
            name=hospital_in.name,
            capacity=hospital_in.capacity,
            available_capacity=hospital_in.available_capacity,
            emergency_available=hospital_in.emergency_available,
            icu_available=hospital_in.icu_available,
            accessibility=hospital_in.accessibility.value,
            status=hospital_in.status,
            location=hospital_in.location.model_dump(),
            source=hospital_in.source.value,
        )
        self.digital_twin.register_hospital(twin_entity)

        self._hospitals[hospital_in.hospital_id] = record
        self._audit_logs[hospital_in.hospital_id] = [
            FacilityAuditEntry(
                actor=actor,
                action="CREATED",
                previous_state=None,
                new_state=record,
                state_version=1,
                details=f"Hospital '{hospital_in.name}' created with capacity {hospital_in.capacity} (available: {hospital_in.available_capacity})",
            )
        ]

        # Add flood exposure evaluation
        record["flood_exposure"] = self.evaluate_flood_exposure(record["location"])
        return record

    def get_hospital(self, hospital_id: str) -> Dict[str, Any]:
        """Retrieve hospital with current state version and flood exposure."""
        if hospital_id not in self._hospitals:
            raise FacilityNotFoundError(f"Hospital '{hospital_id}' not found.")
        record = dict(self._hospitals[hospital_id])
        record["flood_exposure"] = self.evaluate_flood_exposure(record["location"])
        return record

    def list_hospitals(
        self,
        status: Optional[HospitalStatus] = None,
        accessibility: Optional[Accessibility] = None,
        emergency_available: Optional[bool] = None,
        has_available_capacity: Optional[bool] = None,
        sort_by: str = "name",
        sort_desc: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List hospitals with factual filtering, pagination, and deterministic sorting."""
        items = [self.get_hospital(hid) for hid in self._hospitals]

        if status:
            items = [h for h in items if h["status"] == status.value]
        if accessibility:
            items = [h for h in items if h["accessibility"] == accessibility.value]
        if emergency_available is not None:
            items = [h for h in items if h.get("emergency_available") == emergency_available]
        if has_available_capacity is True:
            items = [h for h in items if h.get("available_capacity", 0) > 0]
        elif has_available_capacity is False:
            items = [h for h in items if h.get("available_capacity", 0) == 0]

        # Deterministic sorting
        if sort_by == "available_capacity":
            items.sort(key=lambda x: (x.get("available_capacity", 0), x.get("name", "")), reverse=sort_desc)
        elif sort_by == "updated_at" or sort_by == "last_updated":
            items.sort(key=lambda x: (str(x.get("last_updated", "")), x.get("name", "")), reverse=sort_desc)
        else:
            items.sort(key=lambda x: str(x.get("name", "")), reverse=sort_desc)

        total_count = len(items)
        paginated_items = items[offset : offset + limit]

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "items": paginated_items,
        }

    def update_hospital_capacity(
        self,
        hospital_id: str,
        new_available_capacity: int,
        new_total_capacity: Optional[int] = None,
        new_icu_available: Optional[int] = None,
        expected_state_version: Optional[int] = None,
        actor: str = "COORDINATOR",
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates hospital capacity with optimistic concurrency checks,
        Digital Twin state version increment, and audit trail record.
        """
        record = self.get_hospital(hospital_id)
        current_version = record["state_version"]

        if expected_state_version is not None and expected_state_version != current_version:
            raise FacilityStateVersionConflictError(hospital_id, expected_state_version, current_version)

        target_total = new_total_capacity if new_total_capacity is not None else record["capacity"]
        if new_available_capacity < 0:
            raise ValueError("available_capacity cannot be negative.")
        if target_total < 0:
            raise ValueError("capacity cannot be negative.")
        if new_available_capacity > target_total:
            raise ValueError(
                f"available_capacity ({new_available_capacity}) cannot exceed total capacity ({target_total})."
            )

        previous_state = dict(record)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Emit Digital Twin event
        dt_event = CapacityUpdatedEvent(
            event_id=f"EVT-CAP-{hospital_id}-v{current_version + 1}",
            timestamp=datetime.now(timezone.utc),
            source=EventSource.COMMAND_CENTER,
            facility_type="HOSPITAL",
            facility_id=hospital_id,
            capacity=target_total,
            available_capacity=new_available_capacity,
            icu_available=new_icu_available if new_icu_available is not None else record.get("icu_available"),
            reason=reason,
        )
        self.digital_twin.apply_event(dt_event)

        # Update local authoritative record
        record["capacity"] = target_total
        record["available_capacity"] = new_available_capacity
        if new_icu_available is not None:
            record["icu_available"] = new_icu_available
        record["state_version"] = current_version + 1
        record["last_updated"] = now_iso

        self._hospitals[hospital_id] = record
        self._audit_logs[hospital_id].append(
            FacilityAuditEntry(
                actor=actor,
                action="CAPACITY_UPDATED",
                previous_state=previous_state,
                new_state=record,
                state_version=record["state_version"],
                details=reason or f"Available capacity updated to {new_available_capacity}/{target_total}",
            )
        )

        return self.get_hospital(hospital_id)

    def update_hospital_status(
        self,
        hospital_id: str,
        new_status: HospitalStatus,
        expected_state_version: Optional[int] = None,
        actor: str = "COORDINATOR",
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates hospital status (OPERATIONAL, OVERLOADED, EVACUATING, CLOSED).
        Emits FacilityStatusChangedEvent and records audit entry.
        """
        record = self.get_hospital(hospital_id)
        current_version = record["state_version"]

        if expected_state_version is not None and expected_state_version != current_version:
            raise FacilityStateVersionConflictError(hospital_id, expected_state_version, current_version)

        previous_state = dict(record)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Emit Digital Twin event
        dt_event = FacilityStatusChangedEvent(
            event_id=f"EVT-STATUS-{hospital_id}-v{current_version + 1}",
            timestamp=datetime.now(timezone.utc),
            source=EventSource.COMMAND_CENTER,
            facility_type="HOSPITAL",
            facility_id=hospital_id,
            previous_status=record["status"],
            new_status=new_status.value,
            reason=reason,
        )
        self.digital_twin.apply_event(dt_event)

        record["status"] = new_status.value
        record["state_version"] = current_version + 1
        record["last_updated"] = now_iso

        self._hospitals[hospital_id] = record
        self._audit_logs[hospital_id].append(
            FacilityAuditEntry(
                actor=actor,
                action=f"STATUS_TRANSITION_{new_status.value}",
                previous_state=previous_state,
                new_state=record,
                state_version=record["state_version"],
                details=reason or f"Hospital status transitioned to {new_status.value}",
            )
        )

        return self.get_hospital(hospital_id)

    def get_hospital_history(self, hospital_id: str) -> List[Dict[str, Any]]:
        """Retrieve chronological immutable audit trail for a hospital."""
        if hospital_id not in self._hospitals:
            raise FacilityNotFoundError(f"Hospital '{hospital_id}' not found.")
        return [e.model_dump(mode="json") for e in self._audit_logs.get(hospital_id, [])]

    # =========================================================================
    # SHELTER OPERATIONS
    # =========================================================================

    def create_shelter(
        self,
        shelter_in: Shelter,
        actor: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Creates a new operational shelter entity.
        Validates WGS84 coordinates, bounds (0 <= available <= capacity),
        registers in Digital Twin, and appends audit trail.
        """
        if shelter_in.shelter_id in self._shelters:
            raise ValueError(f"Shelter with ID '{shelter_in.shelter_id}' already exists.")

        lon, lat = shelter_in.location.coordinates[0], shelter_in.location.coordinates[1]
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise ValueError(f"Invalid coordinates [{lon}, {lat}]. Must be within WGS84 bounds.")

        if shelter_in.available_capacity > shelter_in.capacity:
            raise ValueError(
                f"available_capacity ({shelter_in.available_capacity}) cannot exceed total capacity ({shelter_in.capacity})."
            )

        record: Dict[str, Any] = shelter_in.model_dump(mode="json")
        record["state_version"] = 1
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        record["last_updated"] = record["created_at"]

        # Register with Digital Twin
        twin_entity = ShelterEntity(
            shelter_id=shelter_in.shelter_id,
            name=shelter_in.name,
            capacity=shelter_in.capacity,
            available_capacity=shelter_in.available_capacity,
            accessibility=shelter_in.accessibility.value,
            status=shelter_in.status,
            location=shelter_in.location.model_dump(),
            source=shelter_in.source.value,
        )
        self.digital_twin.register_shelter(twin_entity)

        self._shelters[shelter_in.shelter_id] = record
        self._audit_logs[shelter_in.shelter_id] = [
            FacilityAuditEntry(
                actor=actor,
                action="CREATED",
                previous_state=None,
                new_state=record,
                state_version=1,
                details=f"Shelter '{shelter_in.name}' created with capacity {shelter_in.capacity} (available: {shelter_in.available_capacity})",
            )
        ]

        record["flood_exposure"] = self.evaluate_flood_exposure(record["location"])
        return record

    def get_shelter(self, shelter_id: str) -> Dict[str, Any]:
        """Retrieve shelter with current state version and flood exposure."""
        if shelter_id not in self._shelters:
            raise FacilityNotFoundError(f"Shelter '{shelter_id}' not found.")
        record = dict(self._shelters[shelter_id])
        record["flood_exposure"] = self.evaluate_flood_exposure(record["location"])
        return record

    def list_shelters(
        self,
        status: Optional[ShelterStatus] = None,
        accessibility: Optional[Accessibility] = None,
        has_available_capacity: Optional[bool] = None,
        sort_by: str = "name",
        sort_desc: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List shelters with factual filtering, pagination, and deterministic sorting."""
        items = [self.get_shelter(sid) for sid in self._shelters]

        if status:
            items = [s for s in items if s["status"] == status.value]
        if accessibility:
            items = [s for s in items if s["accessibility"] == accessibility.value]
        if has_available_capacity is True:
            items = [s for s in items if s.get("available_capacity", 0) > 0]
        elif has_available_capacity is False:
            items = [s for s in items if s.get("available_capacity", 0) == 0]

        if sort_by == "available_capacity":
            items.sort(key=lambda x: (x.get("available_capacity", 0), x.get("name", "")), reverse=sort_desc)
        elif sort_by == "updated_at" or sort_by == "last_updated":
            items.sort(key=lambda x: (str(x.get("last_updated", "")), x.get("name", "")), reverse=sort_desc)
        else:
            items.sort(key=lambda x: str(x.get("name", "")), reverse=sort_desc)

        total_count = len(items)
        paginated_items = items[offset : offset + limit]

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "items": paginated_items,
        }

    def update_shelter_capacity(
        self,
        shelter_id: str,
        new_available_capacity: int,
        new_total_capacity: Optional[int] = None,
        expected_state_version: Optional[int] = None,
        actor: str = "COORDINATOR",
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates shelter capacity with optimistic concurrency checks,
        Digital Twin state version increment, and audit trail record.
        """
        record = self.get_shelter(shelter_id)
        current_version = record["state_version"]

        if expected_state_version is not None and expected_state_version != current_version:
            raise FacilityStateVersionConflictError(shelter_id, expected_state_version, current_version)

        target_total = new_total_capacity if new_total_capacity is not None else record["capacity"]
        if new_available_capacity < 0:
            raise ValueError("available_capacity cannot be negative.")
        if target_total < 0:
            raise ValueError("capacity cannot be negative.")
        if new_available_capacity > target_total:
            raise ValueError(
                f"available_capacity ({new_available_capacity}) cannot exceed total capacity ({target_total})."
            )

        previous_state = dict(record)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Emit Digital Twin event
        dt_event = CapacityUpdatedEvent(
            event_id=f"EVT-CAP-{shelter_id}-v{current_version + 1}",
            timestamp=datetime.now(timezone.utc),
            source=EventSource.COMMAND_CENTER,
            facility_type="SHELTER",
            facility_id=shelter_id,
            capacity=target_total,
            available_capacity=new_available_capacity,
            reason=reason,
        )
        self.digital_twin.apply_event(dt_event)

        record["capacity"] = target_total
        record["available_capacity"] = new_available_capacity
        record["state_version"] = current_version + 1
        record["last_updated"] = now_iso

        self._shelters[shelter_id] = record
        self._audit_logs[shelter_id].append(
            FacilityAuditEntry(
                actor=actor,
                action="CAPACITY_UPDATED",
                previous_state=previous_state,
                new_state=record,
                state_version=record["state_version"],
                details=reason or f"Shelter available capacity updated to {new_available_capacity}/{target_total}",
            )
        )

        return self.get_shelter(shelter_id)

    def update_shelter_status(
        self,
        shelter_id: str,
        new_status: ShelterStatus,
        expected_state_version: Optional[int] = None,
        actor: str = "COORDINATOR",
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates shelter status (OPEN, AT_CAPACITY, STANDBY, CLOSED).
        Emits FacilityStatusChangedEvent and records audit entry.
        """
        record = self.get_shelter(shelter_id)
        current_version = record["state_version"]

        if expected_state_version is not None and expected_state_version != current_version:
            raise FacilityStateVersionConflictError(shelter_id, expected_state_version, current_version)

        previous_state = dict(record)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Emit Digital Twin event
        dt_event = FacilityStatusChangedEvent(
            event_id=f"EVT-STATUS-{shelter_id}-v{current_version + 1}",
            timestamp=datetime.now(timezone.utc),
            source=EventSource.COMMAND_CENTER,
            facility_type="SHELTER",
            facility_id=shelter_id,
            previous_status=record["status"],
            new_status=new_status.value,
            reason=reason,
        )
        self.digital_twin.apply_event(dt_event)

        record["status"] = new_status.value
        record["state_version"] = current_version + 1
        record["last_updated"] = now_iso

        self._shelters[shelter_id] = record
        self._audit_logs[shelter_id].append(
            FacilityAuditEntry(
                actor=actor,
                action=f"STATUS_TRANSITION_{new_status.value}",
                previous_state=previous_state,
                new_state=record,
                state_version=record["state_version"],
                details=reason or f"Shelter status transitioned to {new_status.value}",
            )
        )

        return self.get_shelter(shelter_id)

    def get_shelter_history(self, shelter_id: str) -> List[Dict[str, Any]]:
        """Retrieve chronological immutable audit trail for a shelter."""
        if shelter_id not in self._shelters:
            raise FacilityNotFoundError(f"Shelter '{shelter_id}' not found.")
        return [e.model_dump(mode="json") for e in self._audit_logs.get(shelter_id, [])]
