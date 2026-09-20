"""
Unit tests for OSM bridge extraction and road association.
"""

import json
from pathlib import Path

import pytest

from geospatial.osm.bridges.models import extract_bridge_from_way, is_osm_way_bridge
from geospatial.osm.roads.parser import parse_osm_payload

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = ROOT_DIR / "data" / "sample" / "osm" / "synthetic_osm_fixture.json"


@pytest.fixture
def parsed_osm():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return parse_osm_payload(payload)


def test_is_osm_way_bridge():
    """Verify bridge detection from tags."""
    assert is_osm_way_bridge({"bridge": "yes"}) is True
    assert is_osm_way_bridge({"bridge": "viaduct"}) is True
    assert is_osm_way_bridge({"man_made": "bridge"}) is True
    assert is_osm_way_bridge({}) is False
    assert is_osm_way_bridge({"highway": "primary"}) is False


def test_extract_bridge_from_way(parsed_osm):
    """Verify bridge entity extraction with road ID relationship."""
    nodes, ways = parsed_osm
    bridge_way = next(w for w in ways if w.way_id == 2002)

    coords = [
        [nodes[1002].longitude, nodes[1002].latitude],
        [nodes[1003].longitude, nodes[1003].latitude],
    ]
    road_id = f"OSM-ROAD-{bridge_way.way_id}"

    bridge = extract_bridge_from_way(bridge_way.way_id, bridge_way.tags, coords, road_id)
    assert bridge is not None
    assert bridge.bridge_id == "BRIDGE-2002"
    assert bridge.road_id == "OSM-ROAD-2002"
    assert bridge.name == "Central River Crossing Bridge"
    assert bridge.layer == 1
    assert bridge.status == "OPEN"
    assert bridge.geometry == coords
