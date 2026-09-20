"""
Domain Exceptions for NEXUS Geospatial Engine.
"""


class GeospatialError(Exception):
    """Base exception for all geospatial operations."""
    pass


class InvalidCoordinateError(GeospatialError):
    """Raised when coordinates fall outside [-180, 180] or [-90, 90], or are non-finite."""
    pass


class InvalidGeometryError(GeospatialError):
    """Raised when a geometry is empty, malformed, or topologically invalid."""
    pass


class UnsupportedGeometryError(GeospatialError):
    """Raised when an unrecognized or unsupported geometry type is encountered."""
    pass


class CRSTransformationError(GeospatialError):
    """Raised when a coordinate reference system transformation fails."""
    pass


class SpatialOperationError(GeospatialError):
    """Raised when a spatial predicate or computation fails."""
    pass
