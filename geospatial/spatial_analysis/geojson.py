"""GeoJSON conversion and FeatureCollection utilities for NEXUS geometries."""

from typing import Any, Dict, List, Optional

import shapely.geometry
from shapely.geometry.base import BaseGeometry

from geospatial.spatial_analysis.validation import validate_geometry


def geometry_to_geojson_dict(geom: BaseGeometry) -> Dict[str, Any]:
    """
    Convert a Shapely geometry to a standard GeoJSON geometry dict.

    Coordinates are guaranteed to follow [longitude, latitude] convention.
    """
    validate_geometry(geom)
    return shapely.geometry.mapping(geom)


def geojson_dict_to_geometry(geojson_dict: Dict[str, Any]) -> BaseGeometry:
    """
    Convert a GeoJSON geometry dictionary to a validated Shapely geometry.
    """
    if not isinstance(geojson_dict, dict) or "type" not in geojson_dict:
        raise ValueError("Invalid GeoJSON geometry dictionary: missing 'type'")
    geom = shapely.geometry.shape(geojson_dict)
    validate_geometry(geom)
    return geom


def create_feature_collection(
    features: List[Dict[str, Any]],
    crs_name: str = "urn:ogc:def:crs:OGC:1.3:CRS84",
) -> Dict[str, Any]:
    """
    Construct a valid GeoJSON FeatureCollection dictionary.

    Args:
        features: List of GeoJSON Feature dictionaries.
        crs_name: Standard CRS identifier, defaults to WGS84 OGC CRS84.

    Returns:
        GeoJSON FeatureCollection dict.
    """
    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": crs_name},
        },
        "features": features,
    }


def create_feature(
    geometry: BaseGeometry,
    properties: Optional[Dict[str, Any]] = None,
    feature_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Construct a valid GeoJSON Feature dictionary from a Shapely geometry.
    """
    feat: Dict[str, Any] = {
        "type": "Feature",
        "geometry": geometry_to_geojson_dict(geometry),
        "properties": properties or {},
    }
    if feature_id is not None:
        feat["id"] = feature_id
    return feat
