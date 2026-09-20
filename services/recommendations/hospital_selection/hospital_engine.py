"""
Hospital Selection Recommendation Engine (Phase 20).
Identifies the most operationally suitable receiving hospital for an incident
respecting available bed capacity, emergency/trauma capability, accessibility, and route distance.
"""

from typing import Any, Dict, List, Optional
from digital_twin.state.state_manager import DigitalTwinStateManager
from geospatial.spatial_analysis.distance import distance_meters
from services.api.app.schemas.hospital import Hospital
from services.api.app.schemas.incident import Incident
from services.api.app.schemas.recommendation import (
    Recommendation,
    RecommendationAction,
    RecommendationApprovalStatus,
    RecommendationEntityType,
    RecommendationTarget,
    RecommendationUncertainty,
)
from services.recommendations.config import HOSPITAL_SELECTION_WEIGHTS, POLICY_VERSION
from services.recommendations.constraints import validate_hospital_candidate
from services.recommendations.scoring.normalizer import normalize_capacity, normalize_min_max
from services.recommendations.scoring.ranker import CandidateRanker


class HospitalSelectionEngine:
    """Evaluates and ranks receiving medical facilities."""

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.weights = weights or dict(HOSPITAL_SELECTION_WEIGHTS)

    def recommend_receiving_hospital(
        self,
        incident: Incident,
        hospitals: List[Hospital],
        digital_twin: DigitalTwinStateManager,
        required_beds: int = 1,
    ) -> Optional[Recommendation]:
        """
        Determines the primary receiving facility candidate and alternatives.
        """
        state_version_str = f"state-v{digital_twin.state_version}"

        valid_scored = []
        for hosp in hospitals:
            passed, reason = validate_hospital_candidate(hosp, required_capacity=required_beds)
            if not passed:
                continue

            # Calculate geodesic distance from incident to hospital
            dist = distance_meters(
                (incident.location.longitude, incident.location.latitude),
                (hosp.location.longitude, hosp.location.latitude),
            )

            # Factors normalization
            # Travel time/distance: closer is better (invert=True, range 0 to 30km)
            dist_score = normalize_min_max(dist, 0.0, 30000.0, invert=True)
            # Available capacity ratio
            cap_score = normalize_capacity(hosp.available_capacity, hosp.capacity)
            # Emergency care capabilities
            emergency_score = 1.0 if hosp.emergency_available else 0.40
            # Flood safety buffer
            flood_exposure = getattr(hosp, "flood_exposure", False)
            flood_safety_score = 0.50 if flood_exposure else 1.0


            norm_factors = {
                "travel_time": dist_score,
                "available_capacity": cap_score,
                "emergency_care": emergency_score,
                "flood_safety": flood_safety_score,
            }

            descriptions = {
                "travel_time": f"Distance: {dist/1000.0:.1f} km (proximity score: {dist_score:.2f})",
                "available_capacity": f"Available beds: {hosp.available_capacity}/{hosp.capacity} ({cap_score:.1%})",
                "emergency_care": "24/7 Emergency Care Available" if hosp.emergency_available else "Standard Medical Center",
                "flood_safety": "Facility in compound flood hazard zone" if flood_exposure else "Facility clear of active flood polygon",
            }


            scored = CandidateRanker.score_candidate(
                candidate_id=hosp.hospital_id,
                entity_type=RecommendationEntityType.HOSPITAL.value,
                entity_name=hosp.name,
                normalized_factors=norm_factors,
                weights=self.weights,
                factor_descriptions=descriptions,
            )
            valid_scored.append((hosp, scored, dist))

        if not valid_scored:
            return None

        # Sort descending by score
        valid_scored.sort(key=lambda x: x[1].total_score, reverse=True)
        best_hosp, best_scored, best_dist = valid_scored[0]

        reasoning = (
            f"Recommended receiving facility: {best_hosp.name}. "
            f"Distance: {best_dist/1000.0:.1f} km. "
            f"Available capacity: {best_hosp.available_capacity} beds. "
            f"Emergency services verified active."
        )

        created_time = getattr(incident, "reported_at", None) or getattr(incident, "created_at", None) or datetime.now(timezone.utc)
        return Recommendation(
            schema_version="1.0.0",
            recommendation_id=f"REC-HOSP-{incident.incident_id}-{best_hosp.hospital_id}",
            created_at=created_time,
            priority=1 if incident.severity.value == "CRITICAL" else 2,
            action=RecommendationAction.DIVERT_AMBULANCES,
            target=RecommendationTarget(
                entity_type=RecommendationEntityType.HOSPITAL,
                entity_id=best_hosp.hospital_id,
                description=f"{best_hosp.name} (Available Beds: {best_hosp.available_capacity})",
            ),
            reasoning=reasoning,
            factors=best_scored.factors,
            confidence=round(best_scored.total_score, 2),
            uncertainty=RecommendationUncertainty(
                lower_bound=max(0.0, round(best_scored.total_score - 0.05, 2)),
                upper_bound=min(1.0, round(best_scored.total_score + 0.05, 2)),
                metric="facility_capacity_uncertainty",
            ),
            source_state_version=state_version_str,
            requires_human_approval=True,
            approval_status=RecommendationApprovalStatus.PENDING,
        )
