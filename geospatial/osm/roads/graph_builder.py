"""
Road Graph Topology Builder.
Constructs deterministic NetworkX and serializable RoadGraphDefinition models from OSM entities.
"""

from typing import Any

import networkx as nx

from geospatial.osm.bridges.models import is_osm_way_bridge
from geospatial.osm.roads.distance import calculate_linestring_length
from geospatial.osm.roads.models import (
    GraphEdge,
    GraphNode,
    OSMNode,
    OSMWay,
    RoadGraphDefinition,
)
from geospatial.osm.roads.normalizer import (
    normalize_accessibility,
    normalize_speed_limit,
)


def parse_oneway_tag(tags: dict[str, Any]) -> str:
    """
    Parse OSM oneway tags.
    Returns:
        'forward' for oneway=yes / 1 / true
        'backward' for oneway=-1 / reverse
        'bidirectional' for oneway=no or absent
    """
    oneway = tags.get("oneway", "").lower().strip()
    highway = tags.get("highway", "").lower().strip()
    junction = tags.get("junction", "").lower().strip()

    if junction == "roundabout":
        return "forward"
    if highway == "motorway":
        # Motorways in OSM are oneway by default unless specified
        if oneway not in ("no", "0", "false"):
            return "forward"

    if oneway in ("yes", "1", "true"):
        return "forward"
    if oneway in ("-1", "reverse"):
        return "backward"
    return "bidirectional"


def build_road_graph(
    nodes_map: dict[int, OSMNode],
    ways: list[OSMWay],
    graph_id: str = "nexus-road-graph",
) -> tuple[nx.MultiDiGraph, RoadGraphDefinition]:
    """
    Construct both a NetworkX MultiDiGraph and serializable RoadGraphDefinition.
    Preserves:
      - LineString geometry on edges
      - Geodesic edge length in meters
      - Directionality (one-way vs bidirectional)
      - Bridge association
      - Highway and speed metadata
    """
    # Deterministic sorting of ways and nodes
    sorted_ways = sorted(ways, key=lambda w: w.way_id)

    # MultiDiGraph supports multiple edges between nodes and directionality
    G = nx.MultiDiGraph(id=graph_id)

    graph_nodes_dict: dict[str, GraphNode] = {}
    graph_edges: list[GraphEdge] = []

    for way in sorted_ways:
        tags = way.tags
        oneway_type = parse_oneway_tag(tags)
        speed_limit = normalize_speed_limit(tags.get("maxspeed"))
        accessibility = normalize_accessibility(tags).value
        road_type = tags.get("highway", "residential")
        is_bridge = is_osm_way_bridge(tags)
        bridge_id = f"BRIDGE-{way.way_id}" if is_bridge else None
        road_id = f"OSM-ROAD-{way.way_id}"

        # Subdivide way nodes into consecutive segments
        for i in range(len(way.nodes) - 1):
            u_id_raw = way.nodes[i]
            v_id_raw = way.nodes[i + 1]

            if u_id_raw not in nodes_map or v_id_raw not in nodes_map:
                continue

            u_node = nodes_map[u_id_raw]
            v_node = nodes_map[v_id_raw]

            u_str = f"NODE-{u_id_raw}"
            v_str = f"NODE-{v_id_raw}"

            # Register graph nodes
            if u_str not in graph_nodes_dict:
                graph_nodes_dict[u_str] = GraphNode(
                    node_id=u_str,
                    longitude=u_node.longitude,
                    latitude=u_node.latitude,
                )
                G.add_node(
                    u_str,
                    longitude=u_node.longitude,
                    latitude=u_node.latitude,
                )

            if v_str not in graph_nodes_dict:
                graph_nodes_dict[v_str] = GraphNode(
                    node_id=v_str,
                    longitude=v_node.longitude,
                    latitude=v_node.latitude,
                )
                G.add_node(
                    v_str,
                    longitude=v_node.longitude,
                    latitude=v_node.latitude,
                )

            segment_coords = [
                [u_node.longitude, u_node.latitude],
                [v_node.longitude, v_node.latitude],
            ]
            length_m = calculate_linestring_length(segment_coords)

            # Determine directions to emit
            directions_to_emit: list[tuple[str, str, str, list[list[float]]]] = []
            if oneway_type == "forward":
                directions_to_emit.append((u_str, v_str, "forward", segment_coords))
            elif oneway_type == "backward":
                reversed_coords = [
                    [v_node.longitude, v_node.latitude],
                    [u_node.longitude, u_node.latitude],
                ]
                directions_to_emit.append((v_str, u_str, "backward", reversed_coords))
            else:  # bidirectional
                directions_to_emit.append((u_str, v_str, "forward", segment_coords))
                reversed_coords = [
                    [v_node.longitude, v_node.latitude],
                    [u_node.longitude, u_node.latitude],
                ]
                directions_to_emit.append((v_str, u_str, "backward", reversed_coords))

            for src, tgt, direction, geom in directions_to_emit:
                edge_id = f"EDGE-{way.way_id}-{src}-{tgt}"
                edge_obj = GraphEdge(
                    edge_id=edge_id,
                    source_node=src,
                    target_node=tgt,
                    road_id=road_id,
                    geometry=geom,
                    length_meters=length_m,
                    directionality=(
                        "bidirectional" if oneway_type == "bidirectional" else direction
                    ),
                    road_type=road_type,
                    accessibility=accessibility,
                    speed_limit_kmh=speed_limit,
                    is_bridge=is_bridge,
                    bridge_id=bridge_id,
                )
                graph_edges.append(edge_obj)

                G.add_edge(
                    src,
                    tgt,
                    key=edge_id,
                    edge_id=edge_id,
                    road_id=road_id,
                    length_meters=length_m,
                    road_type=road_type,
                    accessibility=accessibility,
                    speed_limit_kmh=speed_limit,
                    is_bridge=is_bridge,
                    bridge_id=bridge_id,
                    geometry=geom,
                )

    definition = RoadGraphDefinition(
        nodes=list(graph_nodes_dict.values()),
        edges=graph_edges,
        metadata={
            "graph_id": graph_id,
            "node_count": len(graph_nodes_dict),
            "edge_count": len(graph_edges),
            "crs": "EPSG:4326",
        },
    )

    return G, definition
