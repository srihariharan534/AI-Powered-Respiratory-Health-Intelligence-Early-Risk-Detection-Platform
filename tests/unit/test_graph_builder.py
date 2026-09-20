"""
Unit tests for road graph topology construction and serialization.
"""

import json
from pathlib import Path

import pytest

from geospatial.osm.roads.graph_builder import build_road_graph, parse_oneway_tag
from geospatial.osm.roads.parser import parse_osm_payload

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = ROOT_DIR / "data" / "sample" / "osm" / "synthetic_osm_fixture.json"


@pytest.fixture
def parsed_osm():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return parse_osm_payload(payload)


def test_parse_oneway_tag():
    """Verify oneway tag interpretations."""
    assert parse_oneway_tag({"oneway": "yes"}) == "forward"
    assert parse_oneway_tag({"oneway": "-1"}) == "backward"
    assert parse_oneway_tag({"oneway": "no"}) == "bidirectional"
    assert parse_oneway_tag({}) == "bidirectional"
    assert parse_oneway_tag({"highway": "motorway"}) == "forward"


def test_build_road_graph_topology(parsed_osm):
    """Verify NetworkX graph and serializable definition preserve topology, lengths, and bridges."""
    nodes, ways = parsed_osm
    nx_graph, graph_def = build_road_graph(nodes, ways, graph_id="test-corridor-graph")

    # Nodes check
    assert len(graph_def.nodes) == 4
    assert nx_graph.number_of_nodes() == 4

    # Edges check:
    # Way 2001 (bidirectional): 2 directed edges (1001 <-> 1002)
    # Way 2002 (bidirectional bridge): 2 directed edges (1002 <-> 1003)
    # Way 2003 (oneway=yes): 1 directed edge (1002 -> 1004)
    # Way 2004 (bidirectional service): 2 directed edges (1004 <-> 1001)
    # Total = 2 + 2 + 1 + 2 = 7 edges
    assert len(graph_def.edges) == 7
    assert nx_graph.number_of_edges() == 7

    # One-way preservation check
    assert nx_graph.has_edge("NODE-1002", "NODE-1004")
    assert not nx_graph.has_edge("NODE-1004", "NODE-1002")

    # Bridge metadata check
    bridge_edges = [e for e in graph_def.edges if e.is_bridge]
    assert len(bridge_edges) == 2
    for b_edge in bridge_edges:
        assert b_edge.bridge_id == "BRIDGE-2002"
        assert b_edge.road_id == "OSM-ROAD-2002"

    # Edge length check
    for edge in graph_def.edges:
        assert edge.length_meters > 0.0

    # Serialization test
    serialized = graph_def.model_dump_json()
    assert "test-corridor-graph" in serialized
