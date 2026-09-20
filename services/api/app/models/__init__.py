"""
NEXUS Domain Models Package.
Domain models will be declared in subsequent phases starting with Phase 04.
"""

from services.api.app.database import Base
from services.api.app.models.facility import HospitalModel, ShelterModel
from services.api.app.models.incident import IncidentModel

__all__ = ["Base", "IncidentModel", "HospitalModel", "ShelterModel"]

