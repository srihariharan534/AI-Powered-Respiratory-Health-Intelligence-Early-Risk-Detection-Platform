"""Tests for distance calculations."""

import pytest
from shapely.geometry import LineString, Point

from geospatial.spatial_analysis.distance import distance_meters
from geospatial.spatial_analysis.exceptions import InvalidCoordinateError
from tests.geospatial.fixtures import P1_CENTRAL, P2_EGMORE, P3_MARINA


def test_distance_zero_identical():
    d = distance_meters(P1_CENTRAL, P1_CENTRAL)
    assert d == 0.0


def test_distance_known_points():
    # Distance from Chennai Central (80.2707, 13.0827) to Egmore (80.2610, 13.0732) is ~1.48 km (1400 - 1600m)
    d = distance_meters(P1_CENTRAL, P2_EGMORE)
    assert 1400 < d < 1600

    # Distance to Marina Beach (~3.8 - 4.0 km)
    d_marina = distance_meters(P1_CENTRAL, P3_MARINA)
    assert 3500 < d_marina < 4500


def test_distance_symmetry():
    d1 = distance_meters(P1_CENTRAL, P2_EGMORE)
    d2 = distance_meters(P2_EGMORE, P1_CENTRAL)
    assert pytest.approx(d1, rel=1e-5) == d2


def test_distance_point_to_line():
    line = LineString([(80.270, 13.080), (80.272, 13.085)])
    d = distance_meters(P1_CENTRAL, line)
    assert d >= 0.0
    assert d < 500.0


def test_distance_invalid_coords_rejected():
    bad_point = Point(200.0, 13.0)
    with pytest.raises(InvalidCoordinateError):
        distance_meters(P1_CENTRAL, bad_point)
