"""
NEXUS Digital Twin - Vulnerable Group Entity.
Operational representation of identified vulnerable populations in the emergency theater.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VulnerabilityCategory(str, Enum):
    ELDERLY = "ELDERLY"
    MOBILITY = "MOBILITY"
    HEALTHCARE = "HEALTHCARE"
    SOCIOECONOMIC = "SOCIOECONOMIC"
    CHILDREN = "CHILDREN"
    OTHER = "OTHER"


class VulnerableGroupEntity(BaseModel):
    """
    Operational representation of a vulnerable demographic grouping.
    NOTE: Does NOT compute prioritization or triage scores (owned by Phase 27).
    """
    vulnerable_group_id: str = Field(..., description="Unique vulnerability record ID (e.g. 'VG-001')")
    name: Optional[str] = Field(None, description="Descriptive grouping name or facility")
    category: VulnerabilityCategory = Field(..., description="Vulnerability category")
    count: int = Field(..., description="Estimated number of affected vulnerable individuals", ge=0)
    location: Optional[Dict[str, Any]] = Field(None, description="Spatial coordinates or GeoJSON geometry")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp (UTC)")
    source: str = Field(default="SURVEY", description="Source of vulnerability data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

    model_config = {
        "frozen": False,
        "validate_assignment": True,
    }
