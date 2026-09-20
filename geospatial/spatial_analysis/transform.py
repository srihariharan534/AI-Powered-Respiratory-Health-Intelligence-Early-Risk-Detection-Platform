"""
Coordinate Reference System (CRS) Transformation Module.
Provides robust reprojection between WGS84 (EPSG:4326) and local projected UTM zones.
"""

import math

from pyproj import CRS, Transformer
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from geospatial.spatial_analysis.exceptions import (
    CRSTransformationError,
    InvalidCoordinateError,
)
from geospatial.spatial_analysis.validation import validate_geometry


def get_utm_crs_for_coordinates(longitude: float, latitude: float) -> str:
    """
    Determine the appropriate EPSG code for the WGS84 Universal Transverse Mercator (UTM) zone
    at the specified geographic coordinates.
    """
    if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
        raise InvalidCoordinateError(f"Coordinates ({longitude}, {latitude}) out of bounds for UTM lookup.")

    zone_number = int(math.floor((longitude + 180.0) / 6.0)) + 1
    # Northern hemisphere: EPSG:32600 + zone
    # Southern hemisphere: EPSG:32700 + zone
    epsg_code = (32600 if latitude >= 0 else 32700) + zone_number
    return f"EPSG:{epsg_code}"


def transform_geometry(
    geometry: BaseGeometry,
    source_crs: str = "EPSG:4326",
    target_crs: str = "EPSG:3857",
) -> BaseGeometry:
    """
    Reproject a Shapely geometry from source_crs to target_crs.
    Coordinates must be in (x, y) / (lon, lat) ordering.
    """
    validate_geometry(geometry, crs=source_crs)

    if source_crs == target_crs:
        return geometry

    try:
        src = CRS.from_user_input(source_crs)
        tgt = CRS.from_user_input(target_crs)
        # always_xy=True ensures coordinates are interpreted as (longitude, latitude) or (easting, northing)
        transformer = Transformer.from_crs(src, tgt, always_xy=True)
        reprojected = transform(transformer.transform, geometry)
        validate_geometry(reprojected, crs=target_crs)
        return reprojected
    except Exception as exc:
        raise CRSTransformationError(
            f"Failed to reproject geometry from {source_crs} to {target_crs}: {exc}"
        ) from exc


def to_projected_utm(geometry: BaseGeometry) -> tuple[BaseGeometry, str]:
    """
    Automatically reproject a WGS84 geometry to its local metric UTM projection.
    Returns (projected_geometry, utm_crs_code).
    """
    validate_geometry(geometry)
    centroid = geometry.centroid
    utm_crs = get_utm_crs_for_coordinates(centroid.x, centroid.y)
    projected = transform_geometry(geometry, source_crs="EPSG:4326", target_crs=utm_crs)
    return projected, utm_crs


def to_wgs84(geometry: BaseGeometry, source_crs: str) -> BaseGeometry:
    """
    Reproject a geometry from a specified source CRS back to WGS84 (EPSG:4326).
    """
    return transform_geometry(geometry, source_crs=source_crs, target_crs="EPSG:4326")
