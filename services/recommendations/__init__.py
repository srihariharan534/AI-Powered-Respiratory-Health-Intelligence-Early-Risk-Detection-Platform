"""
NEXUS Operational Recommendations Package (Phase 20).
"""

from services.recommendations.config import (
    HOSPITAL_SELECTION_WEIGHTS,
    INCIDENT_PRIORITY_WEIGHTS,
    POLICY_VERSION,
    ROUTE_SELECTION_WEIGHTS,
    SHELTER_SELECTION_WEIGHTS,
)
from services.recommendations.contracts import (
    GenerateRecommendationRequest,
    RecommendationAuditEntry,
    RecommendationType,
    ScoredCandidate,
)
from services.recommendations.engine import OperationalRecommendationEngine
from services.recommendations.service import (
    RecommendationNotFoundError,
    RecommendationService,
    StaleRecommendationError,
)

__all__ = [
    "HOSPITAL_SELECTION_WEIGHTS",
    "INCIDENT_PRIORITY_WEIGHTS",
    "POLICY_VERSION",
    "ROUTE_SELECTION_WEIGHTS",
    "SHELTER_SELECTION_WEIGHTS",
    "GenerateRecommendationRequest",
    "RecommendationAuditEntry",
    "RecommendationType",
    "ScoredCandidate",
    "OperationalRecommendationEngine",
    "RecommendationNotFoundError",
    "RecommendationService",
    "StaleRecommendationError",
]
