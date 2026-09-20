"""
Geographic & Planar Distance and Length/Area Computation Module.
Distinguishes between geodesic (Haversine/Great Circle) and local UTM projected metric distances.
"""

import math

from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from geospatial.spatial_analysis.transform import to_projected_utm
from geospatial.spatial_analysis.validation import validate_geometry


def distance_meters(
    geom_a: tuple[float, float] | BaseGeometry,
    geom_b: tuple[float, float] | BaseGeometry,
) -> float:
    """
    Calculate distance in meters between two WGS84 coordinates or geometries.
    For two points, uses great-circle Haversine formula.
    For point-to-line, point-to-polygon, or geometry-to-geometry, projects to local UTM
    and calculates minimum Euclidean planar distance.
    """
    if isinstance(geom_a, tuple):
        geom_a = Point(geom_a[0], geom_a[1])
    if isinstance(geom_b, tuple):
        geom_b = Point(geom_b[0], geom_b[1])

    validate_geometry(geom_a)
    validate_geometry(geom_b)

    # Point to point: use geodesic Haversine
    if geom_a.geom_type == "Point" and geom_b.geom_type == "Point":
        lon1, lat1 = geom_a.x, geom_a.y
        lon2, lat2 = geom_b.x, geom_b.y

        r = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)

    # For other geometries (point-to-line, polygon, etc.), reproject to common local UTM
    proj_a, utm_crs = to_projected_utm(geom_a)
    proj_b = to_projected_utm(geom_b)[0]
    return round(float(proj_a.distance(proj_b)), 2)


def geometry_length_meters(geometry: BaseGeometry) -> float:
    """
    Calculate the length of a LineString or MultiLineString in meters
    by reprojecting to local UTM or accumulating geodesic segment distances.
    """
    validate_geometry(geometry)

    if geometry.geom_type in ("LineString", "MultiLineString"):
        projected, _ = to_projected_utm(geometry)
        return round(float(projected.length), 2)
    return 0.0


def polygon_area_sq_meters(geometry: BaseGeometry) -> float:
    """
    Calculate the area of a Polygon or MultiPolygon in square meters
    by reprojecting to local metric UTM.
    """
    validate_geometry(geometry)

    if geometry.geom_type in ("Polygon", "MultiPolygon"):
        projected, _ = to_projected_utm(geometry)
        return round(float(projected.area), 2)
    return 0.0
