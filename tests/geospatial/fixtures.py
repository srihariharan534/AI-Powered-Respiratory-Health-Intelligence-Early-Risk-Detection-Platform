"""
SYNTHETIC TEST FIXTURE — Spatial Analysis Test Fixtures for NEXUS Phase 06.
Contains deterministic mock coordinates and geometries in EPSG:4326.
No live external network or proprietary datasets are accessed.
"""

from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon

# Chennai Central area synthetic benchmarks
CHENNAI_CENTRAL_LON = 80.2707
CHENNAI_CENTRAL_LAT = 13.0827

EGMORE_LON = 80.2610
EGMORE_LAT = 13.0732

MARINA_BEACH_LON = 80.2825
MARINA_BEACH_LAT = 13.0500

# Synthetic Points
P1_CENTRAL = Point(CHENNAI_CENTRAL_LON, CHENNAI_CENTRAL_LAT)
P2_EGMORE = Point(EGMORE_LON, EGMORE_LAT)
P3_MARINA = Point(MARINA_BEACH_LON, MARINA_BEACH_LAT)
P_OUTSIDE = Point(81.0, 14.0)

# Synthetic Flood Extent Polygon surrounding Central & Egmore
# [min_lon, min_lat] to [max_lon, max_lat] bounding box roughly 80.25 to 80.28, 13.07 to 13.09
POLY_FLOOD_ZONE = Polygon([
    (80.250, 13.070),
    (80.280, 13.070),
    (80.280, 13.090),
    (80.250, 13.090),
    (80.250, 13.070),
])

# Synthetic Touching Polygon (shares border at lon=80.280)
POLY_TOUCHING_ZONE = Polygon([
    (80.280, 13.070),
    (80.300, 13.070),
    (80.300, 13.090),
    (80.280, 13.090),
    (80.280, 13.070),
])

# Synthetic Disjoint Polygon (far inland)
POLY_DISJOINT = Polygon([
    (80.100, 13.000),
    (80.120, 13.000),
    (80.120, 13.020),
    (80.100, 13.020),
    (80.100, 13.000),
])

# Synthetic Road LineStrings
# Road crossing the flood zone from west to east
ROAD_CROSSING = LineString([
    (80.240, 13.080),  # starts outside
    (80.260, 13.080),  # inside
    (80.275, 13.080),  # inside
    (80.290, 13.080),  # exits to touching zone
])

# Road strictly inside
ROAD_INSIDE = LineString([
    (80.255, 13.075),
    (80.270, 13.085),
])

# Road strictly outside
ROAD_OUTSIDE = LineString([
    (80.105, 13.005),
    (80.115, 13.015),
])

# MultiLineString & MultiPolygon
MULTI_LINE = MultiLineString([ROAD_INSIDE, ROAD_OUTSIDE])
MULTI_POLY = MultiPolygon([POLY_FLOOD_ZONE, POLY_DISJOINT])
