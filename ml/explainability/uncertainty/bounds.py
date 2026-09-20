"""
Documented thresholds and bounds for uncertainty, data quality, and OOD diagnostics.
"""

from typing import Dict, Tuple

# Physical feature bounds: (min, max)
PHYSICAL_FEATURE_BOUNDS: Dict[str, Tuple[float, float]] = {
    "rainfall_mm_1h": (0.0, 500.0),
    "rainfall_mm_24h": (0.0, 2000.0),
    "elevation_m": (-50.0, 9000.0),
    "distance_to_river_m": (0.0, 100000.0),
    "slope_degrees": (0.0, 90.0),
    "road_density_km": (0.0, 50.0),
    "infrastructure_exposure_count": (0.0, 100.0),
}

# Empirical Standardized Distance Thresholds
# Standardized distance D = sqrt(sum_j z_j^2)
# Under standard normal N(0, I_7), E[D^2] = 7, so typical D ~ sqrt(7) ~= 2.65.
# - D <= 3.2: IN_DISTRIBUTION (expected operational envelope)
# - 3.2 < D <= 4.8: WARNING (unusual or high-consequence combination)
# - D > 4.8: OUT_OF_DISTRIBUTION (extreme tail or non-physical artifact)
DISTANCE_THRESHOLD_WARNING = 3.2
DISTANCE_THRESHOLD_OOD = 4.8
