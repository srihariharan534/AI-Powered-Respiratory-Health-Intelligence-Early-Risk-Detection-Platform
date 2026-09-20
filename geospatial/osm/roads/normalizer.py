"""
OpenStreetMap Highway Normalizer.
Normalizes raw OSM way attributes into canonical NEXUS Road models (Phase 04 schema).
"""

import re
from datetime import datetime, timezone

from geospatial.osm.bridges.models import is_osm_way_bridge
from geospatial.osm.roads.models import OSMNode, OSMWay
from services.api.app.schemas.road import (
    Accessibility,
    LineGeometry,
    Road,
    RoadSource,
    RoadStatus,
    RoadType,
)


def normalize_speed_limit(maxspeed_tag: str | None) -> float | None:
    """
    Parse and normalize OSM maxspeed tag into km/h.
    Handles '30', '50 km/h', '40 mph', etc.
    """
    if not maxspeed_tag:
        return None

    cleaned = maxspeed_tag.strip().lower()
    # Check for mph
    mph_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:mph|miles/h)?$", cleaned)
    if "mph" in cleaned and mph_match:
        try:
            return round(float(mph_match.group(1)) * 1.60934, 1)
        except ValueError:
            return None

    # Check for km/h or raw number
    kmh_match = re.match(r"^(\d+(?:\.\d+)?)(?:\s*(?:km/h|kmh|kph))?$", cleaned)
    if kmh_match:
        try:
            speed = float(kmh_match.group(1))
            if 0.0 <= speed <= 150.0:
                return speed
        except ValueError:
            return None

    return None


def normalize_accessibility(tags: dict[str, str]) -> Accessibility:
    """
    Evaluate accessibility based on access, motor_vehicle, vehicle, and emergency tags.
    """
    access = tags.get("access", "").lower().strip()
    motor_vehicle = tags.get("motor_vehicle", "").lower().strip()
    emergency = tags.get("emergency", "").lower().strip()

    if access == "emergency" or emergency in ("yes", "designated", "only"):
        return Accessibility.EMERGENCY_ONLY

    if access in ("no", "private") or motor_vehicle in ("no", "private"):
        return Accessibility.IMPASSABLE

    if access in ("agricultural", "forestry") or tags.get("surface") in ("sand", "mud"):
        return Accessibility.HIGH_CLEARANCE_ONLY

    return Accessibility.ALL_VEHICLES


def normalize_osm_way_to_road(
    way: OSMWay,
    nodes_map: dict[int, OSMNode],
    source: RoadSource = RoadSource.OSM,
) -> Road | None:
    """
    Transform an OSMWay into a canonical Road contract.
    Returns None if fewer than 2 valid nodes exist in nodes_map.
    """
    coordinates: list[list[float]] = []
    for node_id in way.nodes:
        if node_id in nodes_map:
            node = nodes_map[node_id]
            coordinates.append([node.longitude, node.latitude])

    if len(coordinates) < 2:
        return None

    tags = way.tags
    road_id = f"OSM-ROAD-{way.way_id}"
    name = tags.get("name") or tags.get("ref") or f"Unnamed Road {way.way_id}"

    # Determine road type
    if is_osm_way_bridge(tags):
        road_type = RoadType.BRIDGE
    else:
        raw_highway = tags.get("highway", "residential").lower().strip()
        try:
            road_type = RoadType(raw_highway)
        except ValueError:
            road_type = RoadType.RESIDENTIAL

    # Initial structural state from OSM is OPEN, not real-time disaster status
    status = RoadStatus.OPEN

    accessibility = normalize_accessibility(tags)
    speed_limit = normalize_speed_limit(tags.get("maxspeed"))

    # Estimate capacity per lane if available
    lanes_str = tags.get("lanes", "1")
    try:
        lanes = int(lanes_str)
        capacity = lanes * 750
    except ValueError:
        capacity = 750

    return Road(
        schema_version="1.0.0",
        road_id=road_id,
        name=name,
        road_type=road_type,
        status=status,
        accessibility=accessibility,
        geometry=LineGeometry(type="LineString", coordinates=coordinates),
        speed_limit_kmh=speed_limit,
        capacity_vehicles_per_hour=capacity,
        flood_depth_cm=None,
        last_updated=datetime.now(timezone.utc),
        source=source,
    )
