"""Tests for metric line length and polygon area calculations."""

from geospatial.spatial_analysis.distance import (
    geometry_length_meters,
    polygon_area_sq_meters,
)
from tests.geospatial.fixtures import (
    POLY_FLOOD_ZONE,
    ROAD_CROSSING,
    ROAD_INSIDE,
)


def test_road_length_meters():
    # Length of ROAD_INSIDE must be positive and in reasonable meter range (~1.5 - 2 km)
    length = geometry_length_meters(ROAD_INSIDE)
    assert 1000 < length < 3000

    crossing_length = geometry_length_meters(ROAD_CROSSING)
    assert crossing_length > length


def test_polygon_area_sq_meters():
    # POLY_FLOOD_ZONE is ~0.03 deg lon (~3.25km) by ~0.02 deg lat (~2.21km)
    # Expected area is roughly ~7 square kilometers (7,000,000 sq meters)
    area = polygon_area_sq_meters(POLY_FLOOD_ZONE)
    assert 5_000_000 < area < 9_000_000
