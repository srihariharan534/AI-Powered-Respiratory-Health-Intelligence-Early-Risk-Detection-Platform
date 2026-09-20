"""
SQLAlchemy ORM Model for Incident Entity.
Provides relational and PostGIS spatial persistence for operational incidents.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    Integer,
    JSON,
    String,
    Text,
)

from services.api.app.database import Base
from services.api.app.schemas.incident import (
    IncidentEventType,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)


class IncidentModel(Base):
    """
    Relational representation of an operational incident in the database.
    """
    __tablename__ = "incidents"

    incident_id = Column(String(64), primary_key=True, index=True)
    event_type = Column(SQLEnum(IncidentEventType), nullable=False, index=True)
    severity = Column(SQLEnum(IncidentSeverity), nullable=False, index=True)
    status = Column(SQLEnum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN, index=True)
    priority = Column(Integer, nullable=False, default=1, index=True)

    # GeoAlchemy2 Geometry Point in EPSG:4326
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    latitude = Column(String(32), nullable=False)
    longitude = Column(String(32), nullable=False)

    description = Column(Text, nullable=False)
    reported_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    reported_by = Column(String(128), nullable=False)
    source = Column(SQLEnum(IncidentSource), nullable=False, default=IncidentSource.FIELD_OFFICER, index=True)

    # Structured evidence & metadata
    evidence = Column(JSON, nullable=True)
    operational_metadata = Column(JSON, nullable=True, default=dict)

    # Optimistic concurrency & audit tracking
    state_version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM model to dictionary conforming to canonical Incident schema."""
        return {
            "schema_version": "1.0.0",
            "incident_id": self.incident_id,
            "event_type": self.event_type.value if hasattr(self.event_type, "value") else str(self.event_type),
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "priority": self.priority,
            "location": {
                "type": "Point",
                "coordinates": [float(self.longitude), float(self.latitude)],
            },
            "description": self.description,
            "reported_at": self.reported_at.isoformat() if self.reported_at else None,
            "reported_by": self.reported_by,
            "source": self.source.value if hasattr(self.source, "value") else str(self.source),
            "evidence": self.evidence,
            "state_version": self.state_version,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
