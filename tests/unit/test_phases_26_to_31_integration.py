"""
Comprehensive Integration Test Suite for Mega Phases 26–31 (End-to-End Decision Loop).
Verifies:
1. SMS Ingestion -> Incident Creation -> Digital Twin update.
2. Vulnerability Prioritization across flood-exposed sectors.
3. Decision Replay chronological event preservation.
4. Counterfactual alternative route trade-off comparison.
5. Resource Allocation Optimizer capacity constraint matching.
6. Data Trust Layer status queries.
"""

import pytest
from digital_twin.state.state_manager import DigitalTwinStateManager
from infrastructure.monitoring.data_trust import DataTrustRegistry, DataTrustStatus
from services.api.app.repositories.incident_service import IncidentService
from services.recommendations.counterfactual import CounterfactualEngine
from services.recommendations.decision_replay import DecisionReplayEngine
from services.recommendations.resource_allocation import (
    AvailableResource,
    ResourceAllocationOptimizer,
    SectorRequirement,
)
from services.recommendations.vulnerability_priority.service import VulnerabilityPriorityService
from services.sms.ingestion import SMSIngestionService


def test_complete_decision_loop_integration():
    # 1. State Manager & Services
    dt = DigitalTwinStateManager(initial_version=1)
    incident_service = IncidentService(digital_twin=dt)
    replay_engine = DecisionReplayEngine()
    sms_service = SMSIngestionService(incident_service=incident_service, digital_twin=dt)

    # 2. Ingest Emergency SMS Fallback
    raw_sms = "FLOOD VELACHERY-01 BLOCKED CRITICAL 13.0180 80.2230"
    sms_res = sms_service.ingest_sms(raw_sms)
    assert sms_res.success is True
    replay_engine.record(
        stage="SMS_FALLBACK_INGESTION",
        headline="Field SMS incident ingested into central authority",
        entity_id=sms_res.incident_id,
        state_version=dt.state_version,
    )

    # 3. Vulnerability Prioritization
    sectors = [
        {"zone_id": "ZONE-VELACHERY", "flood_depth_meters": 1.6, "elderly_ratio": 0.28},
        {"zone_id": "ZONE-GUINDY", "flood_depth_meters": 0.2, "elderly_ratio": 0.08},
    ]
    ranked = VulnerabilityPriorityService.rank_zones(sectors)
    assert ranked[0].zone_id == "ZONE-VELACHERY"
    assert ranked[0].priority_level in ["HIGH", "CRITICAL"]

    replay_engine.record(
        stage="VULNERABILITY_PRIORITIZATION",
        headline="Zone Velachery identified as priority sector",
        entity_id="ZONE-VELACHERY",
        state_version=dt.state_version,
    )

    # 4. Resource Allocation Optimization
    sector_req = [
        SectorRequirement(
            sector_id="ZONE-VELACHERY",
            risk_score=ranked[0].combined_risk,
            population=15000,
            boats_needed=2,
            teams_needed=1,
        )
    ]
    resources = [
        AvailableResource(resource_id="BOAT-01", resource_type="BOAT", station_id="STATION-SOUTH"),
        AvailableResource(resource_id="BOAT-02", resource_type="BOAT", station_id="STATION-SOUTH"),
        AvailableResource(resource_id="TEAM-03", resource_type="RESCUE_TEAM", station_id="STATION-CENTRAL"),
    ]
    alloc_res = ResourceAllocationOptimizer.optimize(sector_req, resources)
    assert len(alloc_res.proposals) == 1
    assert alloc_res.proposals[0].coverage_ratio == 1.0
    assert len(alloc_res.proposals[0].allocated_resources) == 3

    # 5. Counterfactual Route Comparison
    routes = [
        {"id": "R1", "name": "Saidapet Main Bridge", "distance_km": 4.2, "time_min": 12.0, "exposure": 0.85, "status": "BLOCKED"},
        {"id": "R2", "name": "Anna Salai Elevated Flyover", "distance_km": 6.8, "time_min": 16.5, "exposure": 0.05, "status": "OPEN"},
    ]
    cf_res = CounterfactualEngine.compare_routes("STATION-SOUTH", "ZONE-VELACHERY", routes)
    assert cf_res.primary_recommendation == "Anna Salai Elevated Flyover"
    assert "flood exposure" in cf_res.trade_off_explanation

    # 6. Data Trust Inspection
    trust_registry = DataTrustRegistry()
    assert trust_registry.get_status("flood_depth_grid").status == DataTrustStatus.FRESH
    assert trust_registry.get_status("what_if_scenario_layer").status == DataTrustStatus.SIMULATED

    # 7. Verify Chronological Replay Timeline
    timeline = replay_engine.get_timeline()
    assert len(timeline) == 2
    assert timeline[0].stage == "SMS_FALLBACK_INGESTION"
    assert timeline[1].stage == "VULNERABILITY_PRIORITIZATION"
