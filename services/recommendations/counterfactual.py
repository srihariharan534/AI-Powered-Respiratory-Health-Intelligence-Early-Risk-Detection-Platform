"""
Counterfactual Decision Comparison Engine (Feature B).
Allows emergency coordinators to evaluate trade-offs between operational alternatives
(e.g., Route A vs Route B, Facility A vs Facility B) across distance, risk, and capacity.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class CounterfactualAlternative(BaseModel):
    option_id: str
    option_name: str
    travel_distance_km: float
    estimated_travel_time_min: float
    flood_exposure_index: float = Field(..., ge=0.0, le=1.0)
    capacity_available: int
    accessibility_status: str
    trade_off_summary: str


class CounterfactualComparisonResult(BaseModel):
    decision_type: str
    primary_recommendation: str
    alternatives: List[CounterfactualAlternative]
    trade_off_explanation: str


class CounterfactualEngine:
    """
    Evaluates multi-criteria trade-offs for human-governed operational alternatives.
    """

    @classmethod
    def compare_routes(
        cls,
        origin: str,
        destination: str,
        routes: List[Dict[str, Any]],
    ) -> CounterfactualComparisonResult:
        alternatives = []
        for r in routes:
            alt = CounterfactualAlternative(
                option_id=r["id"],
                option_name=r["name"],
                travel_distance_km=r["distance_km"],
                estimated_travel_time_min=r["time_min"],
                flood_exposure_index=r["exposure"],
                capacity_available=r.get("capacity", 100),
                accessibility_status=r.get("status", "OPEN"),
                trade_off_summary=r.get("summary", "Standard corridor"),
            )
            alternatives.append(alt)

        # Sort by travel time + exposure penalty
        alternatives.sort(key=lambda a: a.estimated_travel_time_min * (1 + a.flood_exposure_index))

        primary = alternatives[0].option_name if alternatives else "NONE"
        explanation = (
            f"Option '{primary}' provides optimal balance between minimal transit time and flood exposure. "
            "Human decision-maker may choose higher-distance alternatives to maximize life-safety margins."
        )

        return CounterfactualComparisonResult(
            decision_type="EMERGENCY_ROUTING",
            primary_recommendation=primary,
            alternatives=alternatives,
            trade_off_explanation=explanation,
        )
