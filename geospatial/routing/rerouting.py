"""
Dynamic Rerouting Engine for NEXUS (Phase 08).
Evaluates existing route validity against operational state overlays, triggers
rerouting only when necessary using the Phase 07 EmergencyRouter, and explains route deltas.
"""

from typing import List, Optional, Set, Tuple

from pydantic import BaseModel, ConfigDict

from geospatial.routing.constraints import EmergencyRoutingPolicy
from geospatial.routing.models import (
    RouteRequest,
    RouteResult,
    VehicleType,
)
from geospatial.routing.route_comparison import RouteComparison, compare_routes
from geospatial.routing.router import EmergencyRouter
from geospatial.routing.state_overlay import StateOverlay


class ReroutingExplanation(BaseModel):
    """
    Machine-readable explanation metadata for an operational route change.
    Derived purely from deterministic graph differences; zero LLM hallucination.
    """
    model_config = ConfigDict(extra="forbid")
    trigger: str
    affected_roads: List[str]
    invalidation_reasons: List[str]
    distance_change_meters: float
    duration_change_seconds: float
    summary: str


class ReroutingResult(BaseModel):
    """
    Structured outcome of an operational route re-evaluation.
    """
    model_config = ConfigDict(extra="forbid")
    reroute_required: bool
    old_route: RouteResult
    new_route: Optional[RouteResult] = None
    comparison: Optional[RouteComparison] = None
    explanation: Optional[ReroutingExplanation] = None
    trigger: str
    state_version_before: int
    state_version_after: int
    no_path_found: bool = False
    error_code: Optional[str] = None


class DynamicRerouter:
    """
    Orchestrates route validation, dynamic rerouting execution, and route change explanation.
    Reuses the Phase 07 EmergencyRouter and respects the StateOverlay.
    """

    def __init__(self, router: EmergencyRouter, overlay: StateOverlay) -> None:
        self.router = router
        self.overlay = overlay
        # Ensure graph adapter is wired to the overlay
        self.router.graph.overlay = overlay

    def is_route_valid(
        self,
        route: RouteResult,
        vehicle_type: Optional[VehicleType] = None,
        policy: Optional[EmergencyRoutingPolicy] = None,
    ) -> Tuple[bool, List[str], Set[str]]:
        """
        Verify whether an existing RouteResult remains traversable under current operational state.
        Returns:
            (is_valid, list_of_reasons, set_of_affected_road_ids)
        """
        eval_vehicle = vehicle_type or route.vehicle_type
        eval_policy = policy or self.router.policy

        invalid_reasons: List[str] = []
        affected_roads: Set[str] = set()

        for segment in route.segments:
            edge_id = segment.edge_id
            edge_data = self.router.graph.get_edge_by_id(edge_id)

            if edge_data is None:
                invalid_reasons.append(f"Edge '{edge_id}' no longer exists in road graph")
                affected_roads.add(segment.road_id)
                continue

            # Evaluate effective traversability via policy
            traversable, reason = eval_policy.evaluate_edge_traversability(edge_data, eval_vehicle)
            if not traversable:
                road_id = str(edge_data.get("road_id", segment.road_id))
                affected_roads.add(road_id)
                invalid_reasons.append(
                    f"Road '{road_id}' (Edge '{edge_id}') is impassable: {reason}"
                )

        is_valid = len(invalid_reasons) == 0
        return is_valid, invalid_reasons, affected_roads

    def evaluate_and_reroute(
        self,
        current_route: RouteResult,
        trigger_description: str = "Operational state change",
        custom_request: Optional[RouteRequest] = None,
    ) -> ReroutingResult:
        """
        Evaluate route validity against the current StateOverlay.
        If route remains valid: returns unchanged route with reroute_required=False.
        If route is invalidated: recalculates shortest path using Phase 07 EmergencyRouter,
        computes RouteComparison, and formats an explainable ReroutingExplanation.
        """
        state_ver_before = current_route.state_version
        state_ver_after = self.overlay.version

        # 1. Validate route against current state
        is_valid, reasons, affected_roads = self.is_route_valid(current_route)

        # 2. If route is still valid, avoid unnecessary recalculation
        if is_valid:
            return ReroutingResult(
                reroute_required=False,
                old_route=current_route,
                new_route=current_route,
                comparison=None,
                explanation=None,
                trigger=trigger_description,
                state_version_before=state_ver_before,
                state_version_after=state_ver_after,
                no_path_found=False,
            )

        # 3. Re-use original RouteRequest or custom override
        request = custom_request or current_route.request
        if request is None:
            # Fallback reconstruction of request from current_route attributes
            request = RouteRequest(
                origin=current_route.origin,
                destination=current_route.destination,
                vehicle_type=current_route.vehicle_type,
                routing_mode=current_route.routing_mode,
            )

        # 4. Attempt recalculation with Phase 07 EmergencyRouter
        try:
            new_route = self.router.route(request)
        except ValueError:
            # Destination became completely unreachable under current road closures
            explanation = ReroutingExplanation(
                trigger=trigger_description,
                affected_roads=sorted(affected_roads),
                invalidation_reasons=reasons,
                distance_change_meters=0.0,
                duration_change_seconds=0.0,
                summary=f"No viable alternative path exists after closures on: {', '.join(sorted(affected_roads))}",
            )
            return ReroutingResult(
                reroute_required=True,
                old_route=current_route,
                new_route=None,
                comparison=None,
                explanation=explanation,
                trigger=trigger_description,
                state_version_before=state_ver_before,
                state_version_after=state_ver_after,
                no_path_found=True,
                error_code="NO_PATH_AFTER_STATE_CHANGE",
            )

        # 5. Compare old and new routes
        comparison = compare_routes(current_route, new_route)

        # 6. Generate deterministic, machine-readable explanation
        dist_sign = "+" if comparison.distance_delta_meters >= 0 else ""
        dur_sign = "+" if comparison.duration_delta_seconds >= 0 else ""
        summary_text = (
            f"Route recalculated due to {trigger_description}. "
            f"Avoids blocked roads: {', '.join(sorted(affected_roads))}. "
            f"Distance: {dist_sign}{comparison.distance_delta_meters:.1f}m, "
            f"Duration: {dur_sign}{comparison.duration_delta_seconds:.1f}s."
        )

        explanation = ReroutingExplanation(
            trigger=trigger_description,
            affected_roads=sorted(affected_roads),
            invalidation_reasons=reasons,
            distance_change_meters=comparison.distance_delta_meters,
            duration_change_seconds=comparison.duration_delta_seconds,
            summary=summary_text,
        )

        return ReroutingResult(
            reroute_required=True,
            old_route=current_route,
            new_route=new_route,
            comparison=comparison,
            explanation=explanation,
            trigger=trigger_description,
            state_version_before=state_ver_before,
            state_version_after=state_ver_after,
            no_path_found=False,
        )
