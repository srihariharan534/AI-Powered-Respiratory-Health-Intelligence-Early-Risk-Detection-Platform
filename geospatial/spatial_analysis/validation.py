"""
Geometry Validation and Sanitization Module.
Enforces coordinate bounds, finiteness, non-empty topology, and valid geometric invariants.
"""

import math
from typing import Any

from shapely.geometry.base import BaseGeometry

from geospatial.spatial_analysis.exceptions import (
    InvalidCoordinateError,
    InvalidGeometryError,
    UnsupportedGeometryError,
)

SUPPORTED_GEOMETRY_TYPES = {
    "Point",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
}


def validate_coordinates(longitude: float, latitude: float) -> None:
    """
    Validate that longitude and latitude are finite numbers within valid WGS84 ranges:
    longitude: [-180.0, 180.0]
    latitude: [-90.0, 90.0]
    """
    if not (isinstance(longitude, (int, float)) and isinstance(latitude, (int, float))):
        raise InvalidCoordinateError(f"Coordinates must be numeric. Got ({longitude}, {latitude})")

    if math.isnan(longitude) or math.isinf(longitude):
        raise InvalidCoordinateError(f"Longitude must be finite. Got {longitude}")
    if math.isnan(latitude) or math.isinf(latitude):
        raise InvalidCoordinateError(f"Latitude must be finite. Got {latitude}")

    if not (-180.0 <= longitude <= 180.0):
        raise InvalidCoordinateError(
            f"Longitude {longitude} is out of bounds. Must be between -180 and 180 degrees."
        )
    if not (-90.0 <= latitude <= 90.0):
        raise InvalidCoordinateError(
            f"Latitude {latitude} is out of bounds. Must be between -90 and 90 degrees."
        )
    return True


def is_valid_point_coords(longitude: float, latitude: float) -> bool:
    """Check if point coordinates are valid without raising exception."""
    try:
        validate_coordinates(longitude, latitude)
        return True
    except InvalidCoordinateError:
        return False


def validate_geometry(geom: Any, crs: str = "EPSG:4326") -> BaseGeometry:
    """
    Validate that an object is a non-empty, supported, valid Shapely geometry.
    If crs is EPSG:4326, validates that coordinates are within [-180, 180] and [-90, 90].
    Returns the validated Shapely BaseGeometry.
    """
    if not isinstance(geom, BaseGeometry):
        raise UnsupportedGeometryError(f"Object {type(geom)} is not a valid Shapely geometry.")

    geom_type = geom.geom_type
    if geom_type not in SUPPORTED_GEOMETRY_TYPES:
        raise UnsupportedGeometryError(f"Geometry type '{geom_type}' is not supported.")

    if geom.is_empty:
        raise InvalidGeometryError(f"Geometry of type '{geom_type}' cannot be empty.")

    if not geom.is_valid:
        raise InvalidGeometryError(f"Geometry of type '{geom_type}' is invalid: topologically invalid or self-intersecting.")

    # Validate coordinate bounds for WGS84 geometries
    if crs == "EPSG:4326":
        # Check coordinates in envelope
        env = geom.envelope
        if hasattr(env, "exterior") and env.exterior is not None:
            for lon, lat in env.exterior.coords:
                validate_coordinates(lon, lat)
        elif hasattr(geom, "coords"):
            for lon, lat in geom.coords:
                validate_coordinates(lon, lat)

    return geom
