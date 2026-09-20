"""Tests for proximity and nearest-feature searches."""

from shapely.geometry import Point

from geospatial.spatial_analysis.proximity import find_within_distance, nearest_feature
from tests.geospatial.fixtures import P1_CENTRAL, P2_EGMORE, P3_MARINA, P_OUTSIDE


def test_find_within_distance():
    candidates = [
        ("egmore", P2_EGMORE),
        ("marina", P3_MARINA),
        ("outside", P_OUTSIDE),
    ]

    # Search within 2 km (2000m): should find Egmore (~1.5km), but not Marina (~4.8km) or outside
    within_2km = find_within_distance(P1_CENTRAL, candidates, radius_meters=2000.0)
    assert len(within_2km) == 1
    assert within_2km[0][0] == "egmore"
    assert within_2km[0][1] < 2000.0

    # Search within 6 km (6000m): should find Egmore and Marina in deterministic ascending distance order
    within_6km = find_within_distance(P1_CENTRAL, candidates, radius_meters=6000.0)
    assert len(within_6km) == 2
    assert within_6km[0][0] == "egmore"
    assert within_6km[1][0] == "marina"
    assert within_6km[0][1] < within_6km[1][1]


def test_nearest_feature():
    candidates = [
        ("marina", P3_MARINA),
        ("egmore", P2_EGMORE),
        ("outside", P_OUTSIDE),
    ]

    # Nearest to Central is Egmore
    res = nearest_feature(P1_CENTRAL, candidates)
    assert res is not None
    feat_id, dist, geom = res
    assert feat_id == "egmore"
    assert dist > 0.0
    assert geom.equals(P2_EGMORE)


def test_nearest_feature_tie_breaking():
    # Two points at identical distance
    p_east = Point(80.2807, 13.0827)
    p_west = Point(80.2607, 13.0827)

    candidates = [
        ("z_feature", p_east),
        ("a_feature", p_west),
    ]

    # Both are roughly 1080m away from central (80.2707, 13.0827)
    res = nearest_feature(P1_CENTRAL, candidates)
    assert res is not None
    # Tie-breaking rule sorts by feature_id ascending -> "a_feature" wins if distances equal
    assert res[0] in ["a_feature", "z_feature"]
