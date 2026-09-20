"""Spatial proximity operations and nearest-feature searches for NEXUS."""

from typing import List, Optional, Sequence, Tuple

from shapely.geometry.base import BaseGeometry

from geospatial.spatial_analysis.distance import distance_meters
from geospatial.spatial_analysis.validation import validate_geometry


def find_within_distance(
    origin: BaseGeometry,
    candidates: Sequence[Tuple[str, BaseGeometry]],
    radius_meters: float,
) -> List[Tuple[str, float]]:
    """
    Find candidate geometries within a given distance radius (in meters) of origin.

    Args:
        origin: BaseGeometry in EPSG:4326.
        candidates: Sequence of (feature_id, geometry) tuples in EPSG:4326.
        radius_meters: Maximum search radius in meters.

    Returns:
        Deterministic list of (feature_id, distance_meters) tuples sorted by
        distance ascending, then by feature_id ascending.
    """
    validate_geometry(origin)
    if radius_meters < 0:
        raise ValueError(f"radius_meters must be non-negative, got {radius_meters}")

    results: List[Tuple[str, float]] = []
    for feat_id, geom in candidates:
        validate_geometry(geom)
        dist = distance_meters(origin, geom)
        if dist <= radius_meters:
            results.append((feat_id, dist))

    # Deterministic sorting: distance ascending, then feature_id ascending
    results.sort(key=lambda item: (item[1], item[0]))
    return results


def nearest_feature(
    origin: BaseGeometry,
    candidates: Sequence[Tuple[str, BaseGeometry]],
    max_distance_meters: Optional[float] = None,
) -> Optional[Tuple[str, float, BaseGeometry]]:
    """
    Find the nearest candidate feature to an origin geometry.

    Tie-breaking is deterministic: if distances match, features are sorted
    by feature_id ascending.

    Args:
        origin: BaseGeometry in EPSG:4326.
        candidates: Sequence of (feature_id, geometry) tuples in EPSG:4326.
        max_distance_meters: Optional distance cutoff in meters.

    Returns:
        (feature_id, distance_meters, geometry) or None if candidates is empty
        or none within max_distance_meters.
    """
    validate_geometry(origin)
    if not candidates:
        return None

    scored: List[Tuple[str, float, BaseGeometry]] = []
    for feat_id, geom in candidates:
        validate_geometry(geom)
        dist = distance_meters(origin, geom)
        if max_distance_meters is not None and dist > max_distance_meters:
            continue
        scored.append((feat_id, dist, geom))

    if not scored:
        return None

    # Deterministic sorting: distance ascending, then feature_id ascending
    scored.sort(key=lambda item: (item[1], item[0]))
    return scored[0]
