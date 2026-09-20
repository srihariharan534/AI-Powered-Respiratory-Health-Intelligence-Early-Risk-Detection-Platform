"""Tests for metric buffer operations."""

import pytest
from shapely.geometry import Point, Polygon

from geospatial.spatial_analysis.buffer import buffer_geometry
from geospatial.spatial_analysis.distance import distance_meters
from tests.geospatial.fixtures import P1_CENTRAL


def test_buffer_point_meters():
    # Buffer point by 500 meters
    radius = 500.0
    poly = buffer_geometry(P1_CENTRAL, radius)

    assert isinstance(poly, Polygon)
    assert poly.is_valid
    assert not poly.is_empty

    # Center must be contained in the buffer
    assert poly.contains(P1_CENTRAL)

    # Any point on the exterior boundary should be approx 500m from center
    boundary_point = Point(poly.exterior.coords[0])
    d = distance_meters(P1_CENTRAL, boundary_point)
    assert pytest.approx(d, rel=0.05) == radius


def test_buffer_negative_error():
    with pytest.raises(ValueError, match="non-negative"):
        buffer_geometry(P1_CENTRAL, -10.0)


def test_buffer_zero_returns_original():
    res = buffer_geometry(P1_CENTRAL, 0.0)
    assert res.equals(P1_CENTRAL)
