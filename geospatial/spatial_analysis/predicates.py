"""
Spatial Predicates: Intersections, Containment, and Coverings.
"""


from shapely.geometry.base import BaseGeometry

from geospatial.spatial_analysis.validation import validate_geometry


def intersects(geometry_a: BaseGeometry, geometry_b: BaseGeometry) -> bool:
    """Check if geometry A and geometry B intersect."""
    validate_geometry(geometry_a)
    validate_geometry(geometry_b)
    return bool(geometry_a.intersects(geometry_b))


def intersection_geometry(
    geometry_a: BaseGeometry,
    geometry_b: BaseGeometry,
) -> BaseGeometry | None:
    """
    Return the intersecting clipped geometry of A and B, or None if no intersection exists.
    """
    validate_geometry(geometry_a)
    validate_geometry(geometry_b)

    if not geometry_a.intersects(geometry_b):
        return None

    result = geometry_a.intersection(geometry_b)
    if result.is_empty:
        return None
    return result


def batch_intersects(
    target_geometry: BaseGeometry,
    candidates: list[tuple[str, BaseGeometry]],
) -> list[str]:
    """
    Return list of candidate IDs that intersect with target_geometry.
    candidates: list of (id, geometry)
    """
    validate_geometry(target_geometry)
    matching_ids = []
    for cid, geom in candidates:
        validate_geometry(geom)
        if target_geometry.intersects(geom):
            matching_ids.append(cid)
    return sorted(matching_ids)


def contains(container: BaseGeometry, containee: BaseGeometry) -> bool:
    """
    Check if container completely contains containee.
    No points of containee lie in the exterior, and at least one in interior.
    """
    validate_geometry(container)
    validate_geometry(containee)
    return bool(container.contains(containee))


def within(containee: BaseGeometry, container: BaseGeometry) -> bool:
    """Check if containee is completely within container."""
    return contains(container, containee)


def covers(covering_geometry: BaseGeometry, covered_geometry: BaseGeometry) -> bool:
    """
    Check if covering_geometry covers covered_geometry.
    Every point of covered_geometry is a point of covering_geometry (including boundaries).
    """
    validate_geometry(covering_geometry)
    validate_geometry(covered_geometry)
    return bool(covering_geometry.covers(covered_geometry))
