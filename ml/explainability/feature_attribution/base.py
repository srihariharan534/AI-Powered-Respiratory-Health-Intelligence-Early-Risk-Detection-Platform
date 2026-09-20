"""
Base interfaces and metadata definitions for feature attribution.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from ml.explainability.contracts import (
    FeatureAttributionItem,
    GlobalExplanation,
    LocalExplanation,
)
from ml.risk_model.contracts import RiskFeatureRecord

FEATURE_METADATA = {
    "rainfall_mm_1h": {
        "display_name": "1-Hour Rainfall",
        "unit": "mm",
        "description": "Short-term peak rainfall intensity",
        "typical_sign": 1.0,
    },
    "rainfall_mm_24h": {
        "display_name": "24-Hour Cumulative Rainfall",
        "unit": "mm",
        "description": "Total antecedent precipitation accumulating over past day",
        "typical_sign": 1.0,
    },
    "elevation_m": {
        "display_name": "Terrain Elevation",
        "unit": "meters",
        "description": "Height above mean sea level; lower terrain indicates higher flood exposure",
        "typical_sign": -1.0,
    },
    "distance_to_river_m": {
        "display_name": "Distance to River/Drainage",
        "unit": "meters",
        "description": "Proximity to drainage canal or river course",
        "typical_sign": -1.0,
    },
    "slope_degrees": {
        "display_name": "Topographic Slope",
        "unit": "degrees",
        "description": "Ground incline angle affecting drainage runoff velocity",
        "typical_sign": -1.0,
    },
    "road_density_km": {
        "display_name": "Road Corridor Density",
        "unit": "km/km²",
        "description": "Impervious surface concentration within 500m radius",
        "typical_sign": 1.0,
    },
    "infrastructure_exposure_count": {
        "display_name": "Critical Facilities Exposure",
        "unit": "facilities",
        "description": "Count of hospitals, relief shelters, and bridges in immediate vicinity",
        "typical_sign": 1.0,
    },
}


class BaseFeatureExplainer(ABC):
    """Abstract interface for model feature explainers."""

    @abstractmethod
    def explain_local(
        self,
        record: RiskFeatureRecord,
        prediction_id: Optional[str] = None,
    ) -> LocalExplanation:
        """Computes local feature attribution for a single observation."""
        pass

    @abstractmethod
    def explain_global(self) -> GlobalExplanation:
        """Computes global feature importance ranking across population."""
        pass
