"""
NEXUS Digital Twin - Population Entity.
Operational representation of population counts across zones/hexes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PopulationEntity(BaseModel):
    """
    Operational representation of a population unit (ward, census block, or hex).
    Synthetic data must be flagged explicitly via source or metadata.
    """
    population_id: str = Field(..., description="Unique population region identifier (e.g. 'POP-001')")
    location: Optional[Dict[str, Any]] = Field(None, description="Spatial boundaries or centerpoint geometry")
    count: int = Field(..., description="Estimated population count", ge=0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp (UTC)")
    source: str = Field(default="CENSUS", description="Data provenance source (e.g. CENSUS, SIMULATION)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

    model_config = {
        "frozen": False,
        "validate_assignment": True,
    }
