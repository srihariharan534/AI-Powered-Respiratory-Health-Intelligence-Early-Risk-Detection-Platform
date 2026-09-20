"""
Metric Geometry Buffering Module.
Buffers WGS84 geometries in true metric distances (meters) via local projected UTM.
"""

from shapely.geometry.base import BaseGeometry

from geospatial.spatial_analysis.exceptions import SpatialOperationError
from geospatial.spatial_analysis.transform import to_projected_utm, transform_geometry
from geospatial.spatial_analysis.validation import validate_geometry


def buffer_geometry(
    geometry: BaseGeometry,
    distance_meters: float,
    quad_segs: int = 16,
) -> BaseGeometry:
    """
    Buffer a WGS84 geometry by a distance specified in meters.
    Pipeline:
      1. Reproject geometry from WGS84 (EPSG:4326) to appropriate local UTM projection.
      2. Apply buffer in meters using Euclidean planar calculations.
      3. Reproject resulting buffer polygon back to WGS84 (EPSG:4326).
    """
    validate_geometry(geometry)

    if distance_meters < 0:
        raise ValueError(
            f"Buffer distance must be non-negative. Got {distance_meters} meters."
        )

    if distance_meters == 0:
        return geometry

    try:
        # Reproject to local metric UTM
        projected, utm_crs = to_projected_utm(geometry)

        # Buffer in true metric units
        buffered_projected = projected.buffer(distance_meters, quad_segs=quad_segs)

        # Reproject back to WGS84
        buffered_wgs84 = transform_geometry(
            buffered_projected,
            source_crs=utm_crs,
            target_crs="EPSG:4326",
        )
        return validate_geometry(buffered_wgs84)
    except Exception as exc:
        raise SpatialOperationError(f"Failed to buffer geometry by {distance_meters}m: {exc}") from exc
