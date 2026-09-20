"""Tests for containment operations (contains, within, covers)."""

from shapely.geometry import Point

from geospatial.spatial_analysis.predicates import contains, covers, within
from tests.geospatial.fixtures import (
    P1_CENTRAL,
    P_OUTSIDE,
    POLY_FLOOD_ZONE,
    ROAD_CROSSING,
    ROAD_INSIDE,
)


def test_contains_and_within():
    assert contains(POLY_FLOOD_ZONE, P1_CENTRAL) is True
    assert within(P1_CENTRAL, POLY_FLOOD_ZONE) is True

    assert contains(POLY_FLOOD_ZONE, P_OUTSIDE) is False
    assert within(P_OUTSIDE, POLY_FLOOD_ZONE) is False

    assert contains(POLY_FLOOD_ZONE, ROAD_INSIDE) is True
    # Road crossing crosses boundary, so not strictly contained
    assert contains(POLY_FLOOD_ZONE, ROAD_CROSSING) is False


def test_boundary_behavior_contains_vs_covers():
    # Point exactly on boundary of polygon:
    # In DE-9IM, a point ON boundary is covered by polygon, but not strictly contained
    boundary_point = Point(80.250, 13.080)
    assert covers(POLY_FLOOD_ZONE, boundary_point) is True
    # In standard topology, interior containment requires point not on boundary
    assert contains(POLY_FLOOD_ZONE, boundary_point) is False
