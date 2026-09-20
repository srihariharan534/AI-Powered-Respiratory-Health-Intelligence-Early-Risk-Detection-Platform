"""Tests for OSM Road Graph integration with Spatial Analysis Engine."""

from shapely.geometry import LineString

from geospatial.osm.roads.graph_builder import build_road_graph
from geospatial.osm.roads.models import GraphEdge
from geospatial.spatial_analysis.distance import distance_meters, geometry_length_meters
from geospatial.spatial_analysis.geojson import geometry_to_geojson_dict
from geospatial.spatial_analysis.predicates import intersection_geometry, intersects
from geospatial.spatial_analysis.transform import to_projected_utm
from tests.geospatial.fixtures import P1_CENTRAL, POLY_FLOOD_ZONE


def test_osm_road_segment_spatial_analysis():
    # Build a road edge matching OSM graph schema
    coords = [[80.260, 13.080], [80.270, 13.080], [80.280, 13.080]]
    edge = GraphEdge(
        edge_id="osm-way-101-fwd",
        source_node="node-1",
        target_node="node-2",
        road_id="osm-way-101",
        geometry=coords,
        length_meters=2160.0,
        directionality="forward",
        road_type="primary",
        accessibility="emergency_accessible",
    )

    line = LineString(edge.geometry)

    # 1. Geometry length
    calc_len = geometry_length_meters(line)
    assert 2000 < calc_len < 2300

    # 2. Road proximity to point
    dist = distance_meters(P1_CENTRAL, line)
    assert 0 <= dist < 1000

    # 3. Road intersection with flood polygon
    assert intersects(line, POLY_FLOOD_ZONE) is True
    submerged = intersection_geometry(line, POLY_FLOOD_ZONE)
    assert submerged is not None
    assert not submerged.is_empty

    # 4. Road coordinate transformation
    utm_geom, epsg = to_projected_utm(line)
    assert epsg == "EPSG:32644"
    assert utm_geom.geom_type == "LineString"

    # 5. Road GeoJSON conversion
    geojson_dict = geometry_to_geojson_dict(line)
    assert geojson_dict["type"] == "LineString"
    assert list(geojson_dict["coordinates"][0]) == [80.260, 13.080]


def test_osm_graph_consumption():
    # Verify graph can hold and expose road geometries for spatial queries
    from geospatial.osm.roads.models import OSMNode, OSMWay
    nodes_map = {
        1: OSMNode(node_id=1, longitude=80.260, latitude=13.080),
        2: OSMNode(node_id=2, longitude=80.270, latitude=13.080),
    }
    way = OSMWay(way_id=101, nodes=[1, 2], tags={"highway": "secondary"})
    networkx_graph, graph_def = build_road_graph(nodes_map, [way])

    edges_dict = networkx_graph.get_edge_data("NODE-1", "NODE-2")
    assert edges_dict is not None
    # Pick first edge from dict
    first_edge = next(iter(edges_dict.values()))
    geom = LineString(first_edge["geometry"])
    assert intersects(geom, POLY_FLOOD_ZONE) is True
