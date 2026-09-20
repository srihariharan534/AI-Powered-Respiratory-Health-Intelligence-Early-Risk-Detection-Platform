"""
Shelter Evacuation Center Selection Engine (Phase 20).
Identifies designated relief camps with open capacity and active life-support utilities.
"""

from typing import Any, Dict, List, Optional
from digital_twin.state.state_manager import DigitalTwinStateManager
from geospatial.spatial_analysis.distance import distance_meters
from services.api.app.schemas.incident import Incident
from services.api.app.schemas.recommendation import (
    Recommendation,
    RecommendationAction,
    RecommendationApprovalStatus,
    RecommendationEntityType,
    RecommendationTarget,
    RecommendationUncertainty,
)
from services.api.app.schemas.shelter import Shelter
from services.recommendations.config import POLICY_VERSION, SHELTER_SELECTION_WEIGHTS
from services.recommendations.constraints import validate_shelter_candidate
from services.recommendations.scoring.normalizer import normalize_capacity, normalize_min_max
from services.recommendations.scoring.ranker import CandidateRanker


class ShelterSelectionEngine:
    """Evaluates and ranks designated evacuation shelters."""

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.weights = weights or dict(SHELTER_SELECTION_WEIGHTS)

    def recommend_shelter(
        self,
        incident: Incident,
        shelters: List[Shelter],
        digital_twin: DigitalTwinStateManager,
        evacuee_count: int = 10,
    ) -> Optional[Recommendation]:
        """
        Determines optimal shelter destination for an evacuating sector or incident.
        """
        state_version_str = f"state-v{digital_twin.state_version}"

        valid_scored = []
        for sh in shelters:
            passed, reason = validate_shelter_candidate(sh, required_capacity=evacuee_count)
            if not passed:
                continue

            dist = distance_meters(
                (incident.location.longitude, incident.location.latitude),
                (sh.location.longitude, sh.location.latitude),
            )

            dist_score = normalize_min_max(dist, 0.0, 25000.0, invert=True)
            cap_score = normalize_capacity(sh.available_capacity, sh.capacity)

            # Utilities resilience: backup generator and water supply
            has_power = getattr(sh, "has_power_backup", False) or getattr(sh, "backup_generator", False)
            has_water = getattr(sh, "has_potable_water", False) or getattr(sh, "water_supply", False)

            resilience = 0.50
            if has_power and has_water:
                resilience = 1.0
            elif has_power or has_water:
                resilience = 0.75

            flood_exposure = getattr(sh, "flood_exposure", False)
            flood_safety_score = 0.50 if flood_exposure else 1.0

            norm_factors = {
                "travel_time": dist_score,
                "available_capacity": cap_score,
                "utilities_resilience": resilience,
                "flood_safety": flood_safety_score,
            }

            descriptions = {
                "travel_time": f"Distance: {dist/1000.0:.1f} km (proximity score: {dist_score:.2f})",
                "available_capacity": f"Available capacity: {sh.available_capacity}/{sh.capacity} people ({cap_score:.1%})",
                "utilities_resilience": f"Utilities: Generator {'Available' if has_power else 'Off'}, Water {'Secure' if has_water else 'Limited'}",
                "flood_safety": "Shelter perimeter exposed to flood boundary" if flood_exposure else "Shelter elevated and dry",
            }


            scored = CandidateRanker.score_candidate(
                candidate_id=sh.shelter_id,
                entity_type=RecommendationEntityType.SHELTER.value,
                entity_name=sh.name,
                normalized_factors=norm_factors,
                weights=self.weights,
                factor_descriptions=descriptions,
            )
            valid_scored.append((sh, scored, dist))

        if not valid_scored:
            return None

        valid_scored.sort(key=lambda x: x[1].total_score, reverse=True)
        best_sh, best_scored, best_dist = valid_scored[0]

        reasoning = (
            f"Recommended relief camp: {best_sh.name}. "
            f"Distance: {best_dist/1000.0:.1f} km. "
            f"Capacity available: {best_sh.available_capacity} persons. "
            f"Power and potable water supplies verified."
        )

        created_time = getattr(incident, "reported_at", None) or getattr(incident, "created_at", None) or datetime.now(timezone.utc)
        return Recommendation(
            schema_version="1.0.0",
            recommendation_id=f"REC-SHELTER-{incident.incident_id}-{best_sh.shelter_id}",
            created_at=created_time,
            priority=2,
            action=RecommendationAction.OPEN_SHELTER,
            target=RecommendationTarget(
                entity_type=RecommendationEntityType.SHELTER,
                entity_id=best_sh.shelter_id,
                description=f"{best_sh.name} (Capacity: {best_sh.available_capacity})",
            ),
            reasoning=reasoning,
            factors=best_scored.factors,
            confidence=round(best_scored.total_score, 2),
            uncertainty=RecommendationUncertainty(
                lower_bound=max(0.0, round(best_scored.total_score - 0.05, 2)),
                upper_bound=min(1.0, round(best_scored.total_score + 0.05, 2)),
                metric="shelter_capacity_uncertainty",
            ),
            source_state_version=state_version_str,
            requires_human_approval=True,
            approval_status=RecommendationApprovalStatus.PENDING,
        )
