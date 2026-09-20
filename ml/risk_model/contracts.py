"""
Canonical Data Contracts for NEXUS Flood Risk Models (Phase 17).
Defines tabular feature contracts, validation bounds, prediction outputs,
and explainability structures.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RiskPredictionClass(int, Enum):
    LOW_RISK = 0
    HIGH_RISK = 1


class ModelMode(str, Enum):
    REAL_DATA = "REAL_DATA"
    SIMULATION = "SIMULATION"
    DEMO = "DEMO"


class RiskFeatureRecord(BaseModel):
    """
    Validated input feature record for operational flood risk estimation.
    All variables represent measurable environmental or spatial characteristics.
    """
    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1, description="Unique identifier for sample/observation")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of observation")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 Latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 Longitude")

    # Environmental & hydrological features
    rainfall_mm_1h: float = Field(..., ge=0.0, le=500.0, description="1-hour accumulated precipitation in mm")
    rainfall_mm_24h: float = Field(..., ge=0.0, le=2000.0, description="24-hour antecedent rainfall in mm")
    elevation_m: float = Field(..., ge=-50.0, le=9000.0, description="Elevation above mean sea level in meters")
    distance_to_river_m: float = Field(..., ge=0.0, le=100000.0, description="Euclidean/geodesic distance to nearest drainage/river channel in meters")
    slope_degrees: float = Field(..., ge=0.0, le=90.0, description="Topographic slope angle in degrees")

    # Infrastructure exposure features
    road_density_km: float = Field(default=0.0, ge=0.0, le=50.0, description="Road corridor density within 500m radius (km/km2)")
    infrastructure_exposure_count: int = Field(default=0, ge=0, le=100, description="Count of critical facilities (hospitals, shelters, bridges) within 1km")

    # Optional ground-truth target for training / validation
    operational_flood_risk: Optional[int] = Field(default=None, ge=0, le=1, description="Binary target: 0=nominal, 1=operational disruption/inundation >= 15cm")

    @model_validator(mode="after")
    def validate_rainfall_consistency(self) -> "RiskFeatureRecord":
        if self.rainfall_mm_1h > self.rainfall_mm_24h:
            # 1h rain cannot logically exceed 24h total rain
            raise ValueError(
                f"1-hour rainfall ({self.rainfall_mm_1h} mm) cannot exceed 24-hour rainfall ({self.rainfall_mm_24h} mm)"
            )
        return self


class FeatureContribution(BaseModel):
    """Local linear feature attribution for an individual prediction."""
    feature_name: str
    feature_value: float
    standardized_value: float
    coefficient: float
    contribution: float  # coefficient * standardized_value
    direction: Literal["INCREASES_RISK", "DECREASES_RISK", "NEUTRAL"]


class RiskPredictionOutput(BaseModel):
    """Authoritative prediction response for a single feature record."""
    sample_id: str
    risk_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated P(flood_risk=1 | features)")
    predicted_class: RiskPredictionClass = Field(..., description="0=low/non-risk, 1=operational risk")
    model_version: str = Field(..., description="Version of the model artifact that generated this prediction")
    feature_version: str = Field(default="v1.0", description="Feature contract schema version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: ModelMode = Field(default=ModelMode.SIMULATION, description="REAL_DATA, SIMULATION, or DEMO")
    feature_contributions: List[FeatureContribution] = Field(default_factory=list, description="Linear model explainability components")
    uncertainty_note: str = Field(default="Model uncertainty not formally estimated; raw logistic probability reported.")


class ModelMetadata(BaseModel):
    """Audit and governance metadata accompanying every trained model artifact."""
    model_id: str
    model_version: str
    algorithm: str
    target_name: str = "operational_flood_risk"
    target_definition: str
    training_dataset_id: str
    dataset_mode: str
    dataset_fingerprint: Optional[str] = None  # SHA-256
    feature_names: List[str]
    coefficients: Optional[Dict[str, float]] = None
    intercept: Optional[float] = None
    feature_importances: Optional[Dict[str, float]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    metrics: Dict[str, Any]
    comparison_to_baseline: Dict[str, Any]
    training_timestamp: str
    random_seed: int
    limitations: List[str]

