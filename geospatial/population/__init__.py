"""
Population Spatial Foundation for NEXUS.

Establishes structural spatial data contracts for administrative or census population layers.
Does NOT fabricate population counts or demographic attributes.
"""

from dataclasses import dataclass
from typing import Optional

from shapely.geometry.base import BaseGeometry

from geospatial.spatial_analysis.validation import validate_geometry


@dataclass(frozen=True)
class PopulationZone:
    """
    Representation of an administrative zone or ward with population density/counts.
    """
    zone_id: str
    geometry: BaseGeometry  # Polygon or MultiPolygon in EPSG:4326
    population_count: Optional[int] = None
    source: str = "unconfigured"

    def __post_init__(self) -> None:
        validate_geometry(self.geometry)
