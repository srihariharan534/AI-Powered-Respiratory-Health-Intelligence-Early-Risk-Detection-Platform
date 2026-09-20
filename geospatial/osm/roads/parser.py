"""
OpenStreetMap Element and Overpass JSON Parser.
Extracts structured OSM nodes and highway ways from raw OSM payloads.
"""

from typing import Any

from geospatial.osm.roads.models import OSMNode, OSMWay

VALID_HIGHWAYS = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "unclassified",
    "residential",
    "service",
    "living_street",
    "pedestrian",
    "track",
}


def parse_osm_payload(
    payload: dict[str, Any],
    allowed_highways: set[str] | None = None,
) -> tuple[dict[int, OSMNode], list[OSMWay]]:
    """
    Parse an Overpass JSON or OSM element dictionary.
    Returns:
        nodes: mapping of node_id -> OSMNode
        ways: list of OSMWay features matching permitted highway classes.
    """
    elements = payload.get("elements", [])
    highways_filter = allowed_highways or VALID_HIGHWAYS

    nodes: dict[int, OSMNode] = {}
    ways: list[OSMWay] = []

    # First pass: collect all nodes with coordinates
    for elem in elements:
        if elem.get("type") == "node":
            node_id = elem["id"]
            lon = elem.get("lon")
            lat = elem.get("lat")
            if lon is not None and lat is not None:
                nodes[node_id] = OSMNode(
                    node_id=node_id,
                    longitude=float(lon),
                    latitude=float(lat),
                    tags=elem.get("tags", {}),
                )

    # Second pass: collect ways with highway tag
    for elem in elements:
        if elem.get("type") == "way":
            tags = elem.get("tags", {})
            highway_class = tags.get("highway")
            if highway_class and highway_class in highways_filter:
                node_refs = elem.get("nodes", [])
                if len(node_refs) >= 2:
                    ways.append(
                        OSMWay(
                            way_id=elem["id"],
                            nodes=node_refs,
                            tags=tags,
                        )
                    )

    return nodes, ways
