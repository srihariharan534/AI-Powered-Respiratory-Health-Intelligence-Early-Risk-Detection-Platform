"""Tests for GeoJSON conversions and FeatureCollections."""

from shapely.geometry import Point

from geospatial.spatial_analysis.geojson import (
    create_feature,
    create_feature_collection,
    geojson_dict_to_geometry,
    geometry_to_geojson_dict,
)
from tests.geospatial.fixtures import P1_CENTRAL, ROAD_INSIDE


def test_geometry_to_geojson_dict():
    p_dict = geometry_to_geojson_dict(P1_CENTRAL)
    assert p_dict["type"] == "Point"
    # Longitude first, latitude second
    assert list(p_dict["coordinates"]) == [80.2707, 13.0827]

    line_dict = geometry_to_geojson_dict(ROAD_INSIDE)
    assert line_dict["type"] == "LineString"
    assert len(line_dict["coordinates"]) == 2


def test_geojson_dict_to_geometry():
    p_dict = {"type": "Point", "coordinates": [80.2707, 13.0827]}
    geom = geojson_dict_to_geometry(p_dict)
    assert isinstance(geom, Point)
    assert geom.x == 80.2707
    assert geom.y == 13.0827


def test_create_feature_and_collection():
    f1 = create_feature(P1_CENTRAL, properties={"name": "Chennai Central"}, feature_id="feat-1")
    assert f1["type"] == "Feature"
    assert f1["id"] == "feat-1"
    assert f1["properties"]["name"] == "Chennai Central"

    fc = create_feature_collection([f1])
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1
    assert "crs" in fc
