"""
Hard operational constraints filter for candidate entities.
Guarantees impossible or illegal candidates are excluded prior to scoring:
- Closed/collapsed roads or impassable water depth
- Facilities with <= 0 available capacity
- Facilities with CLOSED operational status
- Resolved or cancelled incidents
"""

from typing import Optional, Tuple
from services.api.app.schemas.hospital import Hospital, HospitalStatus
from services.api.app.schemas.incident import Incident, IncidentStatus
from services.api.app.schemas.road import Accessibility, RoadStatus
from services.api.app.schemas.shelter import Shelter, ShelterStatus


def validate_incident_candidate(incident: Incident) -> Tuple[bool, Optional[str]]:
    """Hard constraints check for incident candidate."""
    if incident.status in (IncidentStatus.RESOLVED, IncidentStatus.CANCELLED):
        return False, f"Incident {incident.incident_id} is already {incident.status.value}"
    return True, None


def validate_hospital_candidate(
    hospital: Hospital,
    required_capacity: int = 1,
) -> Tuple[bool, Optional[str]]:
    """Hard constraints check for hospital candidate."""
    if hospital.status == HospitalStatus.CLOSED:
        return False, f"Hospital {hospital.hospital_id} is CLOSED"
    if hospital.available_capacity < required_capacity:
        return False, f"Hospital {hospital.hospital_id} has insufficient available capacity ({hospital.available_capacity} < {required_capacity})"
    if hospital.accessibility == Accessibility.IMPASSABLE:
        return False, f"Hospital {hospital.hospital_id} road access is completely IMPASSABLE"
    return True, None


def validate_shelter_candidate(
    shelter: Shelter,
    required_capacity: int = 1,
) -> Tuple[bool, Optional[str]]:
    """Hard constraints check for shelter candidate."""
    if shelter.status == ShelterStatus.CLOSED:
        return False, f"Shelter {shelter.shelter_id} is CLOSED"
    if shelter.available_capacity < required_capacity:
        return False, f"Shelter {shelter.shelter_id} has insufficient available capacity ({shelter.available_capacity} < {required_capacity})"
    if shelter.accessibility == Accessibility.IMPASSABLE:
        return False, f"Shelter {shelter.shelter_id} access is completely IMPASSABLE"
    return True, None



def validate_road_candidate(
    road_status: RoadStatus,
    accessibility: Accessibility,
    water_depth_cm: float = 0.0,
    vehicle_clearance_cm: float = 30.0,
) -> Tuple[bool, Optional[str]]:
    """Hard constraints check for road candidate."""
    if road_status in (RoadStatus.BLOCKED, RoadStatus.CLOSED):
        return False, f"Road corridor status is {road_status.value}"
    if accessibility == Accessibility.BLOCKED:
        return False, "Road accessibility is classified as BLOCKED"
    if water_depth_cm > vehicle_clearance_cm:
        return False, f"Water depth {water_depth_cm:.1f}cm exceeds emergency clearance threshold {vehicle_clearance_cm:.1f}cm"
    return True, None
