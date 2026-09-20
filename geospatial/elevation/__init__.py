"""
Elevation Foundation for NEXUS.

Future elevation model interface (SRTM, Copernicus DEM, etc.).
Currently unconfigured. No fabricated or synthetic elevation values are generated.
"""

from typing import Optional, Sequence

from shapely.geometry import Point


class ElevationProvider:
    """Interface for elevation sampling."""

    def __init__(self, configured: bool = False):
        self.configured = configured

    def get_elevation(self, point: Point) -> Optional[float]:
        """
        Sample elevation (in meters above sea level) at a given point.
        Returns None when unconfigured or data is unavailable.
        """
        if not self.configured:
            return None
        raise NotImplementedError("Live elevation data source not yet integrated.")

    def sample_elevation(
        self, points: Sequence[Point]
    ) -> Sequence[Optional[float]]:
        """
        Batch sample elevation for multiple points.
        """
        return [self.get_elevation(p) for p in points]


default_elevation_provider = ElevationProvider(configured=False)


def get_elevation(point: Point) -> Optional[float]:
    """Convenience helper returning elevation or None if unconfigured."""
    return default_elevation_provider.get_elevation(point)
