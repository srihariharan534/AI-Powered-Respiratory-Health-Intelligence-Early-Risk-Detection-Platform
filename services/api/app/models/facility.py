"""
SQLAlchemy ORM Models for Hospital and Shelter Entities.
Provides relational and PostGIS spatial persistence for facilities.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Integer,
    JSON,
    String,
)

from services.api.app.database import Base
from services.api.app.schemas.hospital import HospitalSource, HospitalStatus
from services.api.app.schemas.road import Accessibility
from services.api.app.schemas.shelter import ShelterSource, ShelterStatus


class HospitalModel(Base):
    """
    Relational representation of a hospital / medical trauma center.
    """
    __tablename__ = "hospitals"

    hospital_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    status = Column(SQLEnum(HospitalStatus), nullable=False, default=HospitalStatus.OPERATIONAL, index=True)
    accessibility = Column(SQLEnum(Accessibility), nullable=False, default=Accessibility.ALL_VEHICLES, index=True)

    capacity = Column(Integer, nullable=False, default=0)
    available_capacity = Column(Integer, nullable=False, default=0, index=True)
    emergency_available = Column(Boolean, nullable=False, default=True, index=True)
    icu_available = Column(Integer, nullable=False, default=0)

    # PostGIS Point in EPSG:4326
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    latitude = Column(String(32), nullable=False)
    longitude = Column(String(32), nullable=False)

    last_updated = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    source = Column(SQLEnum(HospitalSource), nullable=False, default=HospitalSource.SYNTHETIC_DEMO, index=True)
    operational_metadata = Column(JSON, nullable=True, default=dict)
    state_version = Column(Integer, nullable=False, default=1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM model to dictionary conforming to canonical Hospital schema."""
        return {
            "schema_version": "1.0.0",
            "hospital_id": self.hospital_id,
            "name": self.name,
            "location": {
                "type": "Point",
                "coordinates": [float(self.longitude), float(self.latitude)],
            },
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "accessibility": self.accessibility.value if hasattr(self.accessibility, "value") else str(self.accessibility),
            "capacity": self.capacity,
            "available_capacity": self.available_capacity,
            "emergency_available": self.emergency_available,
            "icu_available": self.icu_available,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "source": self.source.value if hasattr(self.source, "value") else str(self.source),
            "state_version": self.state_version,
        }


class ShelterModel(Base):
    """
    Relational representation of an emergency evacuation shelter or relief camp.
    """
    __tablename__ = "shelters"

    shelter_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    status = Column(SQLEnum(ShelterStatus), nullable=False, default=ShelterStatus.OPEN, index=True)
    accessibility = Column(SQLEnum(Accessibility), nullable=False, default=Accessibility.ALL_VEHICLES, index=True)

    capacity = Column(Integer, nullable=False, default=0)
    available_capacity = Column(Integer, nullable=False, default=0, index=True)
    has_power_backup = Column(Boolean, nullable=False, default=False)
    has_potable_water = Column(Boolean, nullable=False, default=True)

    # PostGIS Point in EPSG:4326
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    latitude = Column(String(32), nullable=False)
    longitude = Column(String(32), nullable=False)

    last_updated = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    source = Column(SQLEnum(ShelterSource), nullable=False, default=ShelterSource.SYNTHETIC_DEMO, index=True)
    operational_metadata = Column(JSON, nullable=True, default=dict)
    state_version = Column(Integer, nullable=False, default=1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM model to dictionary conforming to canonical Shelter schema."""
        return {
            "schema_version": "1.0.0",
            "shelter_id": self.shelter_id,
            "name": self.name,
            "location": {
                "type": "Point",
                "coordinates": [float(self.longitude), float(self.latitude)],
            },
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "accessibility": self.accessibility.value if hasattr(self.accessibility, "value") else str(self.accessibility),
            "capacity": self.capacity,
            "available_capacity": self.available_capacity,
            "has_power_backup": self.has_power_backup,
            "has_potable_water": self.has_potable_water,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "source": self.source.value if hasattr(self.source, "value") else str(self.source),
            "state_version": self.state_version,
        }
