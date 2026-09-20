"""Tests for spatial intersection operations."""

from geospatial.spatial_analysis.predicates import (
    batch_intersects,
    intersection_geometry,
    intersects,
)
from tests.geospatial.fixtures import (
    P1_CENTRAL,
    P_OUTSIDE,
    POLY_DISJOINT,
    POLY_FLOOD_ZONE,
    POLY_TOUCHING_ZONE,
    ROAD_CROSSING,
    ROAD_INSIDE,
    ROAD_OUTSIDE,
)


def test_intersects_boolean():
    assert intersects(P1_CENTRAL, POLY_FLOOD_ZONE) is True
    assert intersects(P_OUTSIDE, POLY_FLOOD_ZONE) is False
    assert intersects(ROAD_CROSSING, POLY_FLOOD_ZONE) is True
    assert intersects(ROAD_INSIDE, POLY_FLOOD_ZONE) is True
    assert intersects(ROAD_OUTSIDE, POLY_FLOOD_ZONE) is False


def test_touching_polygons_intersect_at_boundary():
    # Touching boundary is an intersection (shares line/points)
    assert intersects(POLY_FLOOD_ZONE, POLY_TOUCHING_ZONE) is True
    assert intersects(POLY_FLOOD_ZONE, POLY_DISJOINT) is False


def test_intersection_geometry_clipping():
    clipped = intersection_geometry(ROAD_CROSSING, POLY_FLOOD_ZONE)
    assert clipped is not None
    assert not clipped.is_empty
    # Clipped road portion must be shorter than the whole road
    from geospatial.spatial_analysis.distance import geometry_length_meters
    assert geometry_length_meters(clipped) < geometry_length_meters(ROAD_CROSSING)


def test_intersection_geometry_disjoint():
    clipped = intersection_geometry(ROAD_OUTSIDE, POLY_FLOOD_ZONE)
    assert clipped is None or clipped.is_empty


def test_batch_intersects():
    candidates = [
        ("road_crossing", ROAD_CROSSING),
        ("road_inside", ROAD_INSIDE),
        ("road_outside", ROAD_OUTSIDE),
    ]
    matched = batch_intersects(POLY_FLOOD_ZONE, candidates)
    # road_crossing and road_inside intersect; road_outside does not
    assert matched == ["road_crossing", "road_inside"]
