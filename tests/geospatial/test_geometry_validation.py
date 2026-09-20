"""Tests for geometry and coordinate validation."""

import pytest
from shapely.geometry import LineString, Point, Polygon

from geospatial.spatial_analysis.exceptions import (
    InvalidCoordinateError,
    InvalidGeometryError,
)
from geospatial.spatial_analysis.validation import (
    is_valid_point_coords,
    validate_coordinates,
    validate_geometry,
)


def test_valid_coordinates():
    assert validate_coordinates(80.2707, 13.0827) is True
    assert validate_coordinates(-180.0, -90.0) is True
    assert validate_coordinates(180.0, 90.0) is True
    assert validate_coordinates(0.0, 0.0) is True


def test_invalid_coordinates():
    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(181.0, 13.0)

    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(-180.1, 13.0)

    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(80.0, 91.0)

    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(80.0, -90.1)

    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(float("nan"), 13.0)

    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(80.0, float("inf"))


def test_is_valid_point_coords():
    assert is_valid_point_coords(80.0, 13.0) is True
    assert is_valid_point_coords(200.0, 13.0) is False


def test_valid_geometries():
    p = Point(80.2707, 13.0827)
    assert validate_geometry(p) is p

    line = LineString([(80.0, 13.0), (80.1, 13.1)])
    assert validate_geometry(line) is line

    poly = Polygon([(80.0, 13.0), (80.1, 13.0), (80.1, 13.1), (80.0, 13.1), (80.0, 13.0)])
    assert validate_geometry(poly) is poly


def test_empty_geometry_rejection():
    p = Point()
    with pytest.raises(InvalidGeometryError, match="empty"):
        validate_geometry(p)


def test_out_of_bounds_geometry():
    p = Point(200.0, 13.0)
    with pytest.raises(InvalidCoordinateError):
        validate_geometry(p)


def test_self_intersecting_bowtie_polygon():
    # Bowtie polygon is topologically invalid
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    with pytest.raises(InvalidGeometryError, match="topologically invalid"):
        validate_geometry(bowtie)
