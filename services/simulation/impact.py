"""
NEXUS What-If Simulation Engine - Impact Analysis and Results.
Calculates measurable deltas between baseline state and isolated scenario state,
and generates structured counterfactual causal explanations.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from services.simulation.models import ScenarioLifecycleStatus, WhatIfScenarioType


class FloodImpactDelta(BaseModel):
    """Measurable differences in flood conditions."""
    baseline_flooded_area_sq_meters: float = Field(default=0.0, ge=0.0)
    scenario_flooded_area_sq_meters: float = Field(default=0.0, ge=0.0)
    flooded_area_delta_sq_meters: float = Field(default=0.0)
    newly_flooded_area_sq_meters: float = Field(default=0.0, ge=0.0)
    water_depth_delta_meters: Optional[float] = None


class RoadImpactDelta(BaseModel):
    """Changes in road network traversability."""
    newly_blocked_roads: List[str] = Field(default_factory=list)
    newly_restricted_roads: List[str] = Field(default_factory=list)
    total_roads_affected: int = 0


class RouteImpactDelta(BaseModel):
    """Route impact when evaluated against active emergency paths."""
    route_evaluated: bool = False
    route_invalidated: bool = False
    reroute_successful: bool = False
    baseline_distance_meters: Optional[float] = None
    scenario_distance_meters: Optional[float] = None
    distance_delta_meters: Optional[float] = None
    baseline_duration_seconds: Optional[float] = None
    scenario_duration_seconds: Optional[float] = None
    duration_delta_seconds: Optional[float] = None
    divergence_node: Optional[str] = None
    explanation: Optional[str] = None


class FacilityImpactDelta(BaseModel):
    """Capacity and accessibility changes across hospitals and shelters."""
    facility_id: str
    facility_type: str  # 'HOSPITAL' or 'SHELTER'
    name: Optional[str] = None
    baseline_available_capacity: int
    scenario_available_capacity: int
    capacity_delta: int  # scenario - baseline (usually <= 0)
    status: str


class ResourceImpactDelta(BaseModel):
    """Changes in active rescue units or vehicles."""
    resource_type: str
    baseline_available_quantity: int
    scenario_available_quantity: int
    quantity_delta: int
    affected_team_ids: List[str] = Field(default_factory=list)


class CausalStep(BaseModel):
    """A single link in a traceable counterfactual causal chain."""
    step_number: int
    trigger: str
    consequence: str
    affected_entity: str


class CounterfactualExplanation(BaseModel):
    """
    Transparent, deterministic machine-readable explanation of why changes occurred.
    Zero LLM hallucination: synthesized directly from transition state logs.
    """
    summary: str
    causal_chain: List[CausalStep] = Field(default_factory=list)


class WhatIfScenarioResult(BaseModel):
    """
    Authoritative Result of a What-If Scenario simulation.
    Contains measurable deltas and counterfactual explanations without mutating live state.
    """
    scenario_id: str
    name: str
    scenario_type: WhatIfScenarioType
    mode: str = "SIMULATION"
    status: ScenarioLifecycleStatus
    base_state_version: int
    scenario_state_version: int

    # Impact Deltas
    flood_impact: Optional[FloodImpactDelta] = None
    road_impact: Optional[RoadImpactDelta] = None
    route_impact: Optional[RouteImpactDelta] = None
    facility_impacts: List[FacilityImpactDelta] = Field(default_factory=list)
    resource_impacts: List[ResourceImpactDelta] = Field(default_factory=list)

    # Audit & Counterfactuals
    changed_entity_ids: List[str] = Field(default_factory=list)
    explanation: Optional[CounterfactualExplanation] = None
    warnings: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)

    created_at: datetime
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "frozen": True,
    }
