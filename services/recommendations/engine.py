"""
Master Operational Recommendation Engine (Phase 20).
Coordinates candidate generation, constraint verification, multi-factor scoring,
and explanation integration across incident, hospital, shelter, and route domains.
"""

from typing import Any, Dict, List, Optional
from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.schemas.hospital import Hospital
from services.api.app.schemas.incident import Incident
from services.api.app.schemas.recommendation import Recommendation
from services.api.app.schemas.shelter import Shelter
from services.recommendations.contracts import GenerateRecommendationRequest, RecommendationType
from services.recommendations.evacuation.route_recommendation import RouteRecommendationEngine
from services.recommendations.hospital_selection.hospital_engine import HospitalSelectionEngine
from services.recommendations.incident_priority.priority_engine import IncidentPriorityEngine
from services.recommendations.shelter_selection.shelter_engine import ShelterSelectionEngine


class OperationalRecommendationEngine:
    """Master orchestrator for operational recommendation generation."""

    def __init__(
        self,
        digital_twin: DigitalTwinStateManager,
        route_engine: Optional[RouteRecommendationEngine] = None,
    ) -> None:
        self.digital_twin = digital_twin
        self.incident_engine = IncidentPriorityEngine()
        self.hospital_engine = HospitalSelectionEngine()
        self.shelter_engine = ShelterSelectionEngine()
        self.route_engine = route_engine

    def generate_recommendations(
        self,
        request: GenerateRecommendationRequest,
        incidents: List[Incident],
        hospitals: List[Hospital],
        shelters: List[Shelter],
        risk_scores: Optional[Dict[str, float]] = None,
    ) -> List[Recommendation]:
        """Dispatches generation according to request recommendation_type."""
        if request.recommendation_type == RecommendationType.INCIDENT_PRIORITY:
            return self.incident_engine.prioritize_incidents(
                incidents=incidents,
                digital_twin=self.digital_twin,
                risk_model_output_map=risk_scores,
            )

        elif request.recommendation_type == RecommendationType.HOSPITAL_SELECTION:
            target_incident = next((i for i in incidents if i.incident_id == request.incident_id), None)
            if not target_incident and incidents:
                target_incident = incidents[0]
            if not target_incident:
                return []
            rec = self.hospital_engine.recommend_receiving_hospital(
                incident=target_incident,
                hospitals=hospitals,
                digital_twin=self.digital_twin,
            )
            return [rec] if rec else []

        elif request.recommendation_type == RecommendationType.SHELTER_SELECTION:
            target_incident = next((i for i in incidents if i.incident_id == request.incident_id), None)
            if not target_incident and incidents:
                target_incident = incidents[0]
            if not target_incident:
                return []
            rec = self.shelter_engine.recommend_shelter(
                incident=target_incident,
                shelters=shelters,
                digital_twin=self.digital_twin,
            )
            return [rec] if rec else []

        elif request.recommendation_type == RecommendationType.EVACUATION_ROUTE:
            if not self.route_engine:
                return []
            target_incident = next((i for i in incidents if i.incident_id == request.incident_id), None)
            if not target_incident:
                return []
            # Route to nearest hospital or arbitrary safe shelter
            dest_hosp = hospitals[0] if hospitals else None
            if not dest_hosp:
                return []
            rec = self.route_engine.recommend_route(
                origin=(target_incident.location.longitude, target_incident.location.latitude),
                destination=(dest_hosp.location.longitude, dest_hosp.location.latitude),
                target_description=f"Evacuation from Incident {target_incident.incident_id} to {dest_hosp.name}",
                digital_twin=self.digital_twin,
            )
            return [rec] if rec else []

        return []
