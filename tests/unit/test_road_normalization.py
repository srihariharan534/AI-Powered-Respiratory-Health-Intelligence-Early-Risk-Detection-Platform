"""
Unit tests for OSM highway normalization into canonical Road contract.
"""

import json
from pathlib import Path

import pytest

from geospatial.osm.roads.normalizer import (
    normalize_accessibility,
    normalize_osm_way_to_road,
    normalize_speed_limit,
)
from geospatial.osm.roads.parser import parse_osm_payload
from services.api.app.schemas.road import Accessibility, RoadStatus, RoadType

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = ROOT_DIR / "data" / "sample" / "osm" / "synthetic_osm_fixture.json"


@pytest.fixture
def parsed_osm():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return parse_osm_payload(payload)


def test_speed_limit_normalization():
    """Verify various speed limit formats are converted to numeric km/h."""
    assert normalize_speed_limit("50 km/h") == 50.0
    assert normalize_speed_limit("40") == 40.0
    assert normalize_speed_limit("30 mph") == 48.3
    assert normalize_speed_limit(None) is None
    assert normalize_speed_limit("unposted") is None


def test_accessibility_normalization():
    """Verify emergency and private access tags map to canonical accessibility."""
    assert normalize_accessibility({"access": "emergency"}) == Accessibility.EMERGENCY_ONLY
    assert normalize_accessibility({"access": "private"}) == Accessibility.IMPASSABLE
    assert normalize_accessibility({}) == Accessibility.ALL_VEHICLES


def test_normalize_way_to_canonical_road(parsed_osm):
    """Verify normalizer creates a validated Road model compliant with Phase 04 schema."""
    nodes, ways = parsed_osm
    way_2001 = next(w for w in ways if w.way_id == 2001)

    road = normalize_osm_way_to_road(way_2001, nodes)
    assert road is not None
    assert road.road_id == "OSM-ROAD-2001"
    assert road.name == "West Arterial Road"
    assert road.road_type == RoadType.PRIMARY
    assert road.status == RoadStatus.OPEN
    assert road.accessibility == Accessibility.ALL_VEHICLES
    assert road.speed_limit_kmh == 50.0
    assert road.geometry.type == "LineString"
    assert road.geometry.coordinates == [[80.2650, 13.0810], [80.2707, 13.0827]]
