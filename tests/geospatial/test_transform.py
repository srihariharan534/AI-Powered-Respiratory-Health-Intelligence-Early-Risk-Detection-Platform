"""Tests for CRS transformations."""

import pytest

from geospatial.spatial_analysis.transform import (
    get_utm_crs_for_coordinates,
    to_projected_utm,
    to_wgs84,
    transform_geometry,
)
from tests.geospatial.fixtures import CHENNAI_CENTRAL_LAT, CHENNAI_CENTRAL_LON, P1_CENTRAL


def test_utm_crs_lookup():
    # Chennai is in UTM Zone 44N (EPSG:32644)
    epsg_chennai = get_utm_crs_for_coordinates(CHENNAI_CENTRAL_LON, CHENNAI_CENTRAL_LAT)
    assert epsg_chennai == "EPSG:32644"

    # Southern hemisphere check (e.g. Sydney, Australia 151.2, -33.8) -> Zone 56S (EPSG:32756)
    epsg_sydney = get_utm_crs_for_coordinates(151.2, -33.8)
    assert epsg_sydney == "EPSG:32756"


def test_roundtrip_transformation():
    # WGS84 -> UTM -> WGS84
    utm_geom, epsg = to_projected_utm(P1_CENTRAL)
    assert epsg == "EPSG:32644"
    assert utm_geom.geom_type == "Point"

    # Coordinates in UTM should be large meter values (e.g. Easting ~400,000m, Northing ~1,400,000m)
    assert utm_geom.x > 10000
    assert utm_geom.y > 10000

    back_wgs84 = to_wgs84(utm_geom, epsg)
    assert pytest.approx(back_wgs84.x, abs=1e-5) == CHENNAI_CENTRAL_LON
    assert pytest.approx(back_wgs84.y, abs=1e-5) == CHENNAI_CENTRAL_LAT


def test_identical_crs_returns_same():
    res = transform_geometry(P1_CENTRAL, "EPSG:4326", "EPSG:4326")
    assert res.x == P1_CENTRAL.x
    assert res.y == P1_CENTRAL.y
