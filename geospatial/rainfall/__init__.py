"""
Rainfall Foundation for NEXUS.

Future precipitation observation and gridded rainfall interface (IMD, GPM, radar).
Currently unconfigured. No fabricated or synthetic rainfall observations are generated.
"""

from datetime import datetime
from typing import Optional

from shapely.geometry import Point


class RainfallProvider:
    """Interface for precipitation data queries."""

    def __init__(self, configured: bool = False):
        self.configured = configured

    def get_rainfall(
        self, location: Point, timestamp: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Get precipitation rate or accumulation (mm/hr or mm) at a given location.
        Returns None when unconfigured or data is unavailable.
        """
        if not self.configured:
            return None
        raise NotImplementedError("Live rainfall data source not yet integrated.")


default_rainfall_provider = RainfallProvider(configured=False)


def get_rainfall(
    location: Point, timestamp: Optional[datetime] = None
) -> Optional[float]:
    """Convenience helper returning rainfall or None if unconfigured."""
    return default_rainfall_provider.get_rainfall(location, timestamp)
