"""
NEXUS Spatial Analysis Package — Reusable geospatial computation layer.

Provides foundational geospatial operations:
- Coordinate validation & bounding checks
- CRS transformations (WGS84 EPSG:4326 <-> local metric UTM projections)
- Geodesic & planar distance, line length, polygon area calculations
- Metric geometry buffering
- Spatial predicates (intersects, intersection geometry, batch intersections, contains, within, covers)
- Proximity queries & nearest-feature searches with deterministic tie-breaking
- GeoJSON geometry & FeatureCollection conversions
"""

from geospatial.spatial_analysis.buffer import buffer_geometry
from geospatial.spatial_analysis.distance import (
    distance_meters,
    geometry_length_meters,
    polygon_area_sq_meters,
)
from geospatial.spatial_analysis.exceptions import (
    CRSTransformationError,
    GeospatialError,
    InvalidCoordinateError,
    InvalidGeometryError,
    SpatialOperationError,
    UnsupportedGeometryError,
)
from geospatial.spatial_analysis.geojson import (
    create_feature,
    create_feature_collection,
    geojson_dict_to_geometry,
    geometry_to_geojson_dict,
)
from geospatial.spatial_analysis.predicates import (
    batch_intersects,
    contains,
    covers,
    intersection_geometry,
    intersects,
    within,
)
from geospatial.spatial_analysis.proximity import (
    find_within_distance,
    nearest_feature,
)
from geospatial.spatial_analysis.transform import (
    get_utm_crs_for_coordinates,
    to_projected_utm,
    to_wgs84,
    transform_geometry,
)
from geospatial.spatial_analysis.validation import (
    is_valid_point_coords,
    validate_coordinates,
    validate_geometry,
)

__all__ = [
    "CRSTransformationError",
    "GeospatialError",
    "InvalidCoordinateError",
    "InvalidGeometryError",
    "SpatialOperationError",
    "UnsupportedGeometryError",
    "validate_coordinates",
    "validate_geometry",
    "is_valid_point_coords",
    "get_utm_crs_for_coordinates",
    "transform_geometry",
    "to_projected_utm",
    "to_wgs84",
    "distance_meters",
    "geometry_length_meters",
    "polygon_area_sq_meters",
    "buffer_geometry",
    "intersects",
    "intersection_geometry",
    "batch_intersects",
    "contains",
    "within",
    "covers",
    "find_within_distance",
    "nearest_feature",
    "geometry_to_geojson_dict",
    "geojson_dict_to_geometry",
    "create_feature_collection",
    "create_feature",
]
