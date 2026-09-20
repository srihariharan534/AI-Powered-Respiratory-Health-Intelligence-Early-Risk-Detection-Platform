"""
NEXUS Bridge Extraction Package.
"""

from geospatial.osm.bridges.models import (
    BridgeEntity,
    extract_bridge_from_way,
    is_osm_way_bridge,
)

__all__ = [
    "BridgeEntity",
    "extract_bridge_from_way",
    "is_osm_way_bridge",
]
