"""
Unit tests for OpenStreetMap element and Overpass JSON parsing.
"""

import json
from pathlib import Path

import pytest

from geospatial.osm.roads.parser import parse_osm_payload

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = ROOT_DIR / "data" / "sample" / "osm" / "synthetic_osm_fixture.json"


@pytest.fixture
def raw_osm_payload():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_osm_parser_extracts_nodes_and_ways(raw_osm_payload):
    """Verify parser extracts nodes with valid coordinates and filters highways."""
    nodes, ways = parse_osm_payload(raw_osm_payload)

    assert len(nodes) == 4
    assert 1001 in nodes
    assert nodes[1001].longitude == 80.2650
    assert nodes[1001].latitude == 13.0810

    assert len(ways) == 4
    way_ids = {w.way_id for w in ways}
    assert 2001 in way_ids
    assert 2002 in way_ids
    assert 2003 in way_ids
    assert 2004 in way_ids


def test_osm_parser_empty_payload():
    """Verify parser handles empty payload without error."""
    nodes, ways = parse_osm_payload({"elements": []})
    assert len(nodes) == 0
    assert len(ways) == 0
