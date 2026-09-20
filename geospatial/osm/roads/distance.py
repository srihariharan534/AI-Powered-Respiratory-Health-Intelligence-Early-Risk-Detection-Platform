"""
Geodesic distance calculation module using the Haversine formula.
Returns distance in meters between WGS 84 geographic coordinates.
"""

import math


def calculate_haversine_distance(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
    """
    Calculate the great circle distance between two points
    on the Earth (specified in decimal degrees [lon, lat]).
    Returns:
        Distance in meters.
    """
    # Earth radius in meters
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

    return r * c


def calculate_linestring_length(coordinates: list[list[float]]) -> float:
    """
    Calculate the cumulative distance in meters along a LineString.
    coordinates: [[lon, lat], [lon, lat], ...]
    """
    if len(coordinates) < 2:
        return 0.0

    total_meters = 0.0
    for i in range(len(coordinates) - 1):
        lon1, lat1 = coordinates[i]
        lon2, lat2 = coordinates[i + 1]
        total_meters += calculate_haversine_distance(lon1, lat1, lon2, lat2)

    return round(total_meters, 2)
