"""
Bridge Detection and Extraction Models and Utilities.
Detects bridge features from OSM tags and constructs normalized bridge models.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BridgeEntity(BaseModel):
    """Normalized bridge entity associated with a road way."""
    model_config = ConfigDict(extra="forbid")
    bridge_id: str
    road_id: str
    name: str
    geometry: list[list[float]] = Field(..., min_length=2)  # [[lon, lat], ...]
    layer: int = 1
    status: str = "OPEN"
    source: str = "osm"


def is_osm_way_bridge(tags: dict[str, Any]) -> bool:
    """Check if an OSM way represents a bridge."""
    bridge_tag = tags.get("bridge", "").lower().strip()
    man_made = tags.get("man_made", "").lower().strip()

    if bridge_tag in ("yes", "viaduct", "aqueduct", "cantilever", "suspension", "movable"):
        return True
    if man_made == "bridge":
        return True
    return False


def extract_bridge_from_way(
    way_id: int,
    tags: dict[str, Any],
    coordinates: list[list[float]],
    road_id: str,
) -> BridgeEntity | None:
    """Extract a BridgeEntity if the OSM way attributes represent a bridge."""
    if not is_osm_way_bridge(tags):
        return None

    bridge_id = f"BRIDGE-{way_id}"
    name = tags.get("name", f"Bridge {way_id}")
    layer_str = tags.get("layer", "1")
    try:
        layer = int(layer_str)
    except ValueError:
        layer = 1

    return BridgeEntity(
        bridge_id=bridge_id,
        road_id=road_id,
        name=name,
        geometry=coordinates,
        layer=layer,
        status="OPEN",
        source="osm",
    )
