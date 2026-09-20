"""
NEXUS What-If Simulation Engine - Executor.
Coordinates isolated scenario forks, reuses Phase 10 flood simulation,
Phase 08 dynamic rerouting, and computes counterfactual impact without
ever mutating the live Digital Twin.
"""

from typing import List, Optional

import networkx as nx
from shapely.geometry import shape

from digital_twin.entities import BridgeStatus, RescueTeamStatus
from digital_twin.events import (
    BridgeStatusChangedEvent,
    CapacityUpdatedEvent,
    EventSource,
    FloodUpdatedEvent,
    RoadStatusChangedEvent,
)
from digital_twin.state.state_manager import DigitalTwinStateManager
from geospatial.flood import (
    ElevationGrid,
    FloodScenario,
    FloodSimulationEngine,
    evaluate_road_exposure,
)
from geospatial.flood import (
    ScenarioType as FloodScenarioType,
)
from geospatial.flood import (
    SimulationMode as FloodSimMode,
)
from geospatial.routing import (
    DynamicRerouter,
    EmergencyRouter,
    RouteRequest,
    RouteResult,
    RoutingGraphAdapter,
)
from services.api.app.schemas.road import RoadStatus
from services.simulation.impact import (
    CausalStep,
    CounterfactualExplanation,
    FacilityImpactDelta,
    FloodImpactDelta,
    ResourceImpactDelta,
    RoadImpactDelta,
    RouteImpactDelta,
    WhatIfScenarioResult,
)
from services.simulation.models import (
    BridgeFailureModification,
    FloodLevelModification,
    HospitalCapacityModification,
    ResourceShortageModification,
    ScenarioLifecycleStatus,
    ShelterCapacityModification,
    WhatIfScenario,
)

from services.simulation.validator import validate_scenario_against_state


class WhatIfScenarioEngine:
    """
    NEXUS What-If Scenario Orchestration Engine.
    Executes counterfactual scenarios strictly against isolated, forked simulation states.
    Guarantees zero mutation to live operational truth.
    """

    def __init__(
        self,
        live_state_manager: DigitalTwinStateManager,
        routing_graph: Optional[nx.MultiDiGraph] = None,
        elevation_grid: Optional[ElevationGrid] = None,
    ) -> None:
        self.live_state_manager = live_state_manager
        self.routing_graph = routing_graph
        self.elevation_grid = elevation_grid

    def execute_preview(
        self,
        scenario: WhatIfScenario,
        test_route: Optional[RouteResult] = None,
        test_route_request: Optional[RouteRequest] = None,
    ) -> WhatIfScenarioResult:
        """
        Executes a What-If Scenario in preview mode:
        1. Validates scenario against live state (raises on version mismatch).
        2. Forks an isolated scenario Digital Twin and routing overlay.
        3. Applies modifications sequentially to the forked twin.
        4. Reuses Phase 10 Flood Simulation and Phase 08 Dynamic Rerouting if applicable.
        5. Computes impact deltas and counterfactual causal chain.
        6. Safely returns WhatIfScenarioResult while the forked twin is discarded.
        """
        # 1. Validation against live state
        validate_scenario_against_state(scenario, self.live_state_manager)

        # 2. Fork state isolation (Zero mutation to live state)
        isolated_twin = self.live_state_manager.fork()
        isolated_overlay = isolated_twin.routing_overlay

        # Snapshot baseline metrics for comparison
        base_hospitals = {h.hospital_id: h for h in self.live_state_manager.list_entities("hospitals")}
        base_shelters = {s.shelter_id: s for s in self.live_state_manager.list_entities("shelters")}
        base_roads = {r.road_id: r for r in self.live_state_manager.list_entities("roads")}
        base_teams = {t.rescue_team_id: t for t in self.live_state_manager.list_entities("rescue_teams")}


        changed_entities: List[str] = []
        causal_steps: List[CausalStep] = []
        warnings: List[str] = []
        assumptions: List[str] = list(scenario.assumptions)

        flood_impact: Optional[FloodImpactDelta] = None
        road_impact: Optional[RoadImpactDelta] = None
        route_impact: Optional[RouteImpactDelta] = None
        facility_impacts: List[FacilityImpactDelta] = []
        resource_impacts: List[ResourceImpactDelta] = []

        step_counter = 1

        # 3. Apply modifications sequentially to isolated state
        for mod in scenario.modifications:
            if isinstance(mod, BridgeFailureModification):
                bridge_evt = BridgeStatusChangedEvent(
                    event_id=f"SCEN-EVT-{scenario.scenario_id}-B-{mod.bridge_id}",
                    bridge_id=mod.bridge_id,
                    new_status=BridgeStatus.BLOCKED,
                    propagate_to_road=mod.propagate_to_road,
                    source=EventSource.SIMULATION,
                    reason=f"SCENARIO [{scenario.scenario_id}]: Simulated failure of bridge {mod.bridge_id}",
                )
                res = isolated_twin.apply_event(bridge_evt)
                if res.applied:
                    changed_entities.append(mod.bridge_id)
                    causal_steps.append(CausalStep(
                        step_number=step_counter,
                        trigger=f"Hypothetical failure of Bridge {mod.bridge_id}",
                        consequence=f"Bridge {mod.bridge_id} transitioned to BLOCKED",
                        affected_entity=mod.bridge_id,
                    ))
                    step_counter += 1

                    # Check causal road closure
                    bridge = isolated_twin.get_bridge(mod.bridge_id)
                    if bridge and bridge.road_id:
                        changed_entities.append(bridge.road_id)
                        causal_steps.append(CausalStep(
                            step_number=step_counter,
                            trigger=f"Bridge {mod.bridge_id} failure cascade",
                            consequence=f"Associated Road {bridge.road_id} transitioned to BLOCKED",
                            affected_entity=bridge.road_id,
                        ))
                        step_counter += 1

            elif isinstance(mod, HospitalCapacityModification):
                base_hosp = base_hospitals.get(mod.hospital_id)
                cap_evt = CapacityUpdatedEvent(
                    event_id=f"SCEN-EVT-{scenario.scenario_id}-H-{mod.hospital_id}",
                    facility_type="HOSPITAL",
                    facility_id=mod.hospital_id,
                    capacity=base_hosp.capacity if base_hosp else 100,
                    available_capacity=mod.available_capacity,
                    icu_available=mod.icu_available,
                    source=EventSource.SIMULATION,
                )
                res = isolated_twin.apply_event(cap_evt)
                if res.applied:
                    changed_entities.append(mod.hospital_id)
                    delta = mod.available_capacity - (base_hosp.available_capacity if base_hosp else 0)
                    facility_impacts.append(FacilityImpactDelta(
                        facility_id=mod.hospital_id,
                        facility_type="HOSPITAL",
                        name=base_hosp.name if base_hosp else None,
                        baseline_available_capacity=base_hosp.available_capacity if base_hosp else 0,
                        scenario_available_capacity=mod.available_capacity,
                        capacity_delta=delta,
                        status="CAPACITY_REDUCED" if delta < 0 else "CAPACITY_CHANGED",
                    ))
                    causal_steps.append(CausalStep(
                        step_number=step_counter,
                        trigger=f"Hypothetical capacity change for Hospital {mod.hospital_id}",
                        consequence=f"Available capacity reduced by {-delta} beds to {mod.available_capacity}",
                        affected_entity=mod.hospital_id,
                    ))
                    step_counter += 1

            elif isinstance(mod, ShelterCapacityModification):
                base_shelt = base_shelters.get(mod.shelter_id)
                cap_evt = CapacityUpdatedEvent(
                    event_id=f"SCEN-EVT-{scenario.scenario_id}-S-{mod.shelter_id}",
                    facility_type="SHELTER",
                    facility_id=mod.shelter_id,
                    capacity=base_shelt.capacity if base_shelt else 200,
                    available_capacity=mod.available_capacity,
                    source=EventSource.SIMULATION,
                )
                res = isolated_twin.apply_event(cap_evt)
                if res.applied:
                    changed_entities.append(mod.shelter_id)
                    delta = mod.available_capacity - (base_shelt.available_capacity if base_shelt else 0)
                    facility_impacts.append(FacilityImpactDelta(
                        facility_id=mod.shelter_id,
                        facility_type="SHELTER",
                        name=base_shelt.name if base_shelt else None,
                        baseline_available_capacity=base_shelt.available_capacity if base_shelt else 0,
                        scenario_available_capacity=mod.available_capacity,
                        capacity_delta=delta,
                        status="CAPACITY_REDUCED" if delta < 0 else "CAPACITY_CHANGED",
                    ))
                    causal_steps.append(CausalStep(
                        step_number=step_counter,
                        trigger=f"Hypothetical capacity change for Shelter {mod.shelter_id}",
                        consequence=f"Available capacity reduced by {-delta} spots to {mod.available_capacity}",
                        affected_entity=mod.shelter_id,
                    ))
                    step_counter += 1

            elif isinstance(mod, ResourceShortageModification):

                # Apply resource reduction across rescue teams in isolated state
                current_available = sum(1 for t in base_teams.values() if t.status == RescueTeamStatus.AVAILABLE)
                delta = mod.available_quantity - current_available
                affected_teams = []
                if delta < 0:
                    teams_to_disable = abs(delta)
                    for team in isolated_twin.list_entities("rescue_teams"):
                        if teams_to_disable <= 0:
                            break
                        if team.status == RescueTeamStatus.AVAILABLE:
                            team.status = RescueTeamStatus.OFF_DUTY
                            isolated_twin._rescue_teams[team.rescue_team_id] = team
                            affected_teams.append(team.rescue_team_id)
                            teams_to_disable -= 1

                resource_impacts.append(ResourceImpactDelta(
                    resource_type=mod.resource_type,
                    baseline_available_quantity=current_available,
                    scenario_available_quantity=mod.available_quantity,
                    quantity_delta=delta,
                    affected_team_ids=affected_teams,
                ))
                causal_steps.append(CausalStep(
                    step_number=step_counter,
                    trigger=f"Hypothetical shortage of {mod.resource_type}",
                    consequence=f"Operational units decreased from {current_available} to {mod.available_quantity}",
                    affected_entity=mod.resource_type,
                ))
                step_counter += 1

            elif isinstance(mod, FloodLevelModification):
                # Reuse Phase 10 Flood Simulation Engine
                sim_scenario = self._create_phase10_flood_scenario(scenario.scenario_id, mod)
                flood_engine = FloodSimulationEngine(elevation_grid=self.elevation_grid)
                extent = flood_engine.simulate(sim_scenario)

                # Ingest flood update into isolated twin
                flood_evt = FloodUpdatedEvent(
                    event_id=f"SCEN-EVT-{scenario.scenario_id}-FLOOD",
                    flood_zone_id=extent.flood_zone_id,
                    name=sim_scenario.name,
                    geometry=extent.geometry,
                    severity=extent.severity,
                    water_depth_m=extent.maximum_depth_m,
                    source=EventSource.SIMULATION,
                )
                isolated_twin.apply_event(flood_evt)
                changed_entities.append(extent.flood_zone_id)

                flood_impact = FloodImpactDelta(
                    baseline_flooded_area_sq_meters=0.0,
                    scenario_flooded_area_sq_meters=extent.area_sq_meters,
                    flooded_area_delta_sq_meters=extent.area_sq_meters,
                    newly_flooded_area_sq_meters=extent.area_sq_meters,
                    water_depth_delta_meters=extent.maximum_depth_m,
                )
                causal_steps.append(CausalStep(
                    step_number=step_counter,
                    trigger="Hypothetical flood expansion",
                    consequence=f"Flooded area increased by {extent.area_sq_meters:,.0f} m² (max depth {extent.maximum_depth_m or 0.0:.2f}m)",
                    affected_entity=extent.flood_zone_id,
                ))
                step_counter += 1

                # Check road exposure and apply closures in isolated state if configured
                newly_closed_roads = []
                for road in isolated_twin.list_entities("roads"):
                    # Check if road geometry is available in metadata or line geometry
                    road_geom = road.metadata.get("geometry")
                    if road_geom:
                        geom = shape(road_geom) if isinstance(road_geom, dict) else road_geom
                        exp = evaluate_road_exposure(
                            road=road,
                            road_geom=geom,
                            flood_extent=extent,
                            closure_threshold_m=mod.road_closure_threshold_meters,
                            auto_close=mod.auto_close_roads,
                        )
                        if exp.closure_recommended:
                            close_evt = RoadStatusChangedEvent(
                                event_id=f"SCEN-EVT-{scenario.scenario_id}-R-{road.road_id}",
                                road_id=road.road_id,
                                new_status=RoadStatus.BLOCKED,
                                source=EventSource.SIMULATION,
                                reason=exp.closure_reason or "Submerged above vehicle threshold",
                                caused_by_event_id=flood_evt.event_id,
                            )
                            res = isolated_twin.apply_event(close_evt)
                            if res.applied:
                                newly_closed_roads.append(road.road_id)
                                changed_entities.append(road.road_id)

                if newly_closed_roads:
                    causal_steps.append(CausalStep(
                        step_number=step_counter,
                        trigger="Flood water level exceeded vehicle clearance threshold",
                        consequence=f"Roads {newly_closed_roads} transitioned to BLOCKED",
                        affected_entity=str(newly_closed_roads),
                    ))
                    step_counter += 1

        # 4. Road Network Impact Assessment
        scen_roads = {r.road_id: r for r in isolated_twin.list_entities("roads")}
        newly_blocked = [
            rid for rid, r in scen_roads.items()
            if r.status == RoadStatus.BLOCKED and (rid not in base_roads or base_roads[rid].status != RoadStatus.BLOCKED)
        ]
        newly_restricted = [
            rid for rid, r in scen_roads.items()
            if r.status == RoadStatus.RESTRICTED and (rid not in base_roads or base_roads[rid].status != RoadStatus.RESTRICTED)
        ]
        road_impact = RoadImpactDelta(
            newly_blocked_roads=newly_blocked,
            newly_restricted_roads=newly_restricted,
            total_roads_affected=len(newly_blocked) + len(newly_restricted),
        )

        # 5. Routing Evaluation (Phase 08 Dynamic Rerouting reuse)
        if test_route is not None and self.routing_graph is not None and isolated_overlay is not None:
            adapter = RoutingGraphAdapter(self.routing_graph, overlay=isolated_overlay)
            router = EmergencyRouter(adapter)
            rerouter = DynamicRerouter(router, isolated_overlay)

            # Check if test_route crosses any newly blocked edges/roads
            is_valid, invalid_reasons, _ = rerouter.is_route_valid(test_route)
            if not is_valid:
                reroute_res = rerouter.evaluate_and_reroute(
                    current_route=test_route,
                    trigger_description=f"What-If Scenario [{scenario.scenario_id}] road/bridge failure",
                )
                if reroute_res.reroute_required and reroute_res.new_route is not None:
                    comp = reroute_res.comparison
                    route_impact = RouteImpactDelta(
                        route_evaluated=True,
                        route_invalidated=True,
                        reroute_successful=True,
                        baseline_distance_meters=test_route.distance_meters,
                        scenario_distance_meters=reroute_res.new_route.distance_meters,
                        distance_delta_meters=comp.distance_delta_meters if comp else None,
                        baseline_duration_seconds=test_route.estimated_duration_seconds,
                        scenario_duration_seconds=reroute_res.new_route.estimated_duration_seconds,
                        duration_delta_seconds=comp.duration_delta_seconds if comp else None,
                        divergence_node=reroute_res.new_route.path_nodes[0] if reroute_res.new_route.path_nodes else None,
                        explanation=reroute_res.explanation.summary if reroute_res.explanation else "Route diverted around blocked infrastructure",
                    )
                    causal_steps.append(CausalStep(
                        step_number=step_counter,
                        trigger="Active route intercepted by blocked infrastructure",
                        consequence=f"Route invalidated; dynamically rerouted (delta: {route_impact.distance_delta_meters:+.1f}m)",
                        affected_entity="ACTIVE_ROUTE",
                    ))
                    step_counter += 1
                else:
                    route_impact = RouteImpactDelta(
                        route_evaluated=True,
                        route_invalidated=True,
                        reroute_successful=False,
                        explanation="Network severed: NO_PATH_AFTER_STATE_CHANGE",
                    )
                    warnings.append("Scenario completely severs connectivity for active emergency route")
            else:
                route_impact = RouteImpactDelta(
                    route_evaluated=True,
                    route_invalidated=False,
                    reroute_successful=True,
                    baseline_distance_meters=test_route.distance_meters,
                    scenario_distance_meters=test_route.distance_meters,
                    distance_delta_meters=0.0,
                    explanation="Route unaffected by scenario modifications",
                )

        # 6. Synthesize Counterfactual Explanation
        explanation_summary = (
            f"Scenario '{scenario.name}' evaluated against Digital Twin v{scenario.base_state_version}: "
            f"{len(changed_entities)} entities modified. "
        )
        if road_impact and road_impact.newly_blocked_roads:
            explanation_summary += f"{len(road_impact.newly_blocked_roads)} roads blocked. "
        if route_impact and route_impact.route_invalidated:
            explanation_summary += f"Route required dynamic diversion ({route_impact.distance_delta_meters:+.1f}m). "
        if facility_impacts:
            explanation_summary += f"{len(facility_impacts)} medical facilities affected. "

        counterfactual = CounterfactualExplanation(
            summary=explanation_summary.strip(),
            causal_chain=causal_steps,
        )

        return WhatIfScenarioResult(
            scenario_id=scenario.scenario_id,
            name=scenario.name,
            scenario_type=scenario.scenario_type,
            status=ScenarioLifecycleStatus.COMPLETED,
            base_state_version=scenario.base_state_version,
            scenario_state_version=isolated_twin.state_version,
            flood_impact=flood_impact,
            road_impact=road_impact,
            route_impact=route_impact,
            facility_impacts=facility_impacts,
            resource_impacts=resource_impacts,
            changed_entity_ids=sorted(list(set(changed_entities))),
            explanation=counterfactual,
            warnings=warnings,
            assumptions=assumptions,
            created_at=scenario.created_at,
        )

    def _create_phase10_flood_scenario(
        self,
        base_id: str,
        mod: FloodLevelModification,
    ) -> FloodScenario:
        """Adapts a What-If FloodLevelModification into a Phase 10 FloodScenario."""
        if mod.flood_polygon is not None:
            return FloodScenario(
                scenario_id=f"scen-fl-{base_id}",
                name="Hypothetical Flood Polygon",
                scenario_type=FloodScenarioType.EXPLICIT_POLYGON,
                flood_polygon=mod.flood_polygon,
                explicit_depth_m=mod.explicit_depth_meters or 1.0,
                road_closure_depth_threshold_m=mod.road_closure_threshold_meters,
                auto_close_roads=mod.auto_close_roads,
                mode=FloodSimMode.SIMULATION,
            )
        elif mod.water_level_delta_meters is not None:
            return FloodScenario(
                scenario_id=f"scen-fl-{base_id}",
                name=f"Hypothetical Flood +{mod.water_level_delta_meters}m",
                scenario_type=FloodScenarioType.DEPTH_INCREMENT,
                baseline_water_level_m=80.0,  # Standard baseline or from terrain
                depth_increment_m=mod.water_level_delta_meters,
                road_closure_depth_threshold_m=mod.road_closure_threshold_meters,
                auto_close_roads=mod.auto_close_roads,
                mode=FloodSimMode.SIMULATION,
            )
        else:
            return FloodScenario(
                scenario_id=f"scen-fl-{base_id}",
                name="Hypothetical Absolute Water Level",
                scenario_type=FloodScenarioType.WATER_LEVEL,
                water_level_m=mod.absolute_water_level_meters or 85.0,
                road_closure_depth_threshold_m=mod.road_closure_threshold_meters,
                auto_close_roads=mod.auto_close_roads,
                mode=FloodSimMode.SIMULATION,
            )
