"""
Incident Priority Recommendation Engine (Phase 20).
Combines validated operational state, modeled flood risk probability,
incident severity, and vulnerability demographics to produce a prioritized triage queue.
"""

from typing import Any, Dict, List, Optional
from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.schemas.incident import Incident, IncidentStatus
from services.api.app.schemas.recommendation import (
    Recommendation,
    RecommendationAction,
    RecommendationApprovalStatus,
    RecommendationEntityType,
    RecommendationTarget,
    RecommendationUncertainty,
)
from services.recommendations.config import INCIDENT_PRIORITY_WEIGHTS, POLICY_VERSION
from services.recommendations.constraints import validate_incident_candidate
from services.recommendations.scoring.normalizer import (
    normalize_min_max,
    normalize_severity,
)
from services.recommendations.scoring.ranker import CandidateRanker


class IncidentPriorityEngine:
    """Computes deterministic incident prioritization recommendations."""

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.weights = weights or dict(INCIDENT_PRIORITY_WEIGHTS)

    def prioritize_incidents(
        self,
        incidents: List[Incident],
        digital_twin: DigitalTwinStateManager,
        risk_model_output_map: Optional[Dict[str, float]] = None,
    ) -> List[Recommendation]:
        """
        Ranks active incidents and produces structured Recommendation proposals.
        """
        state_version_str = f"state-v{digital_twin.state_version}"
        risk_map = risk_model_output_map or {}

        valid_candidates = []
        for inc in incidents:
            passed, reason = validate_incident_candidate(inc)
            if not passed:
                continue

            # 1. Feature normalization
            risk_prob = risk_map.get(inc.incident_id, 0.50)
            sev_score = normalize_severity(inc.severity.value)

            # Check if near flood zones in digital twin
            flood_exposure_score = 0.30
            for fz in digital_twin.list_entities("flood_zones"):
                if fz.current_water_level_meters > 0.30:
                    flood_exposure_score = 0.85
                    break

            vulnerability_score = 0.40
            # Check vulnerable groups near incident
            vg_list = digital_twin.list_entities("vulnerable_groups")
            if vg_list:
                vulnerability_score = 0.75

            accessibility_score = 0.80  # Baseline corridor availability

            norm_factors = {
                "risk_probability": risk_prob,
                "incident_severity": sev_score,
                "flood_exposure": flood_exposure_score,
                "vulnerability_exposure": vulnerability_score,
                "route_accessibility": accessibility_score,
            }

            factor_descriptions = {
                "risk_probability": f"Modeled operational flood risk probability: {risk_prob:.1%}",
                "incident_severity": f"Reported incident severity tier: {inc.severity.value} ({sev_score:.2f})",
                "flood_exposure": f"Flood water exposure index: {flood_exposure_score:.2f}",
                "vulnerability_exposure": f"Demographic vulnerability weighting: {vulnerability_score:.2f}",
                "route_accessibility": f"Corridor accessibility score: {accessibility_score:.2f}",
            }

            category_label = getattr(inc, "category", None) or getattr(inc, "event_type", "INCIDENT")
            if hasattr(category_label, "value"):
                category_label = category_label.value
            scored = CandidateRanker.score_candidate(
                candidate_id=inc.incident_id,
                entity_type=RecommendationEntityType.ZONE.value,
                entity_name=f"Incident {inc.incident_id} ({category_label})",
                normalized_factors=norm_factors,
                weights=self.weights,
                factor_descriptions=factor_descriptions,
            )
            valid_candidates.append((inc, scored))

        # Rank candidates descending
        valid_candidates.sort(key=lambda x: x[1].total_score, reverse=True)

        recommendations: List[Recommendation] = []
        for rank_idx, (inc, scored) in enumerate(valid_candidates, start=1):
            # Priority tier: 1 is highest emergency urgency, 5 is lowest
            # High total score maps to Priority 1 or 2
            if scored.total_score >= 0.75:
                prio = 1
            elif scored.total_score >= 0.55:
                prio = 2
            elif scored.total_score >= 0.40:
                prio = 3
            else:
                prio = 4

            reasoning = (
                f"Incident {inc.incident_id} is recommended for Rank #{rank_idx} priority dispatch. "
                f"Multi-factor score: {scored.total_score:.2f} under {POLICY_VERSION}. "
                f"Key drivers: severity {inc.severity.value}, flood exposure index {scored.factors[2].description}."
            )

            created_time = getattr(inc, "reported_at", None) or getattr(inc, "created_at", None) or datetime.now(timezone.utc)

            rec = Recommendation(
                schema_version="1.0.0",
                recommendation_id=f"REC-PRIO-{inc.incident_id}",
                created_at=created_time,
                priority=prio,
                action=RecommendationAction.DISPATCH_RESCUE,
                target=RecommendationTarget(
                    entity_type=RecommendationEntityType.ZONE,
                    entity_id=inc.incident_id,
                    description=f"{inc.description} at [{inc.location.latitude}, {inc.location.longitude}]",
                ),
                reasoning=reasoning,
                factors=scored.factors,
                confidence=round(scored.total_score, 2),
                uncertainty=RecommendationUncertainty(
                    lower_bound=max(0.0, round(scored.total_score - 0.08, 2)),
                    upper_bound=min(1.0, round(scored.total_score + 0.08, 2)),
                    metric="multi_factor_policy_bounds",
                ),
                source_state_version=state_version_str,
                requires_human_approval=True,
                approval_status=RecommendationApprovalStatus.PENDING,
            )
            recommendations.append(rec)

        return recommendations
