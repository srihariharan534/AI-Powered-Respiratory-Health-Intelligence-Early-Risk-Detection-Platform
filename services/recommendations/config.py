"""
Configuration and Policy Weights for NEXUS Operational Recommendation Engine (Phase 20).
All weights are explicitly versioned, documented, and deterministic.
"""

from typing import Dict

POLICY_VERSION = "policy-v1.0"

# Multi-factor weights for Incident Operational Priority Scoring
# All weights sum to 1.0
INCIDENT_PRIORITY_WEIGHTS: Dict[str, float] = {
    "risk_probability": 0.30,       # Modeled operational flood risk probability
    "incident_severity": 0.25,      # Life-safety impact tier (CRITICAL, HIGH, MEDIUM, LOW)
    "flood_exposure": 0.20,         # Direct inundation depth / polygon intersection
    "vulnerability_exposure": 0.15, # Presence of vulnerable or mobility-impaired populations
    "route_accessibility": 0.10,    # Feasibility and safety of incoming transit corridors
}

# Multi-factor weights for Hospital Receiving Facility Selection
# All weights sum to 1.0
HOSPITAL_SELECTION_WEIGHTS: Dict[str, float] = {
    "travel_time": 0.35,            # Shortest transit duration from incident
    "available_capacity": 0.30,     # Verified bed/triage surge availability
    "emergency_care": 0.20,         # Level 1 Trauma / 24x7 emergency service availability
    "flood_safety": 0.15,           # Absence of immediate compound flood hazard
}

# Multi-factor weights for Shelter Evacuation Center Selection
# All weights sum to 1.0
SHELTER_SELECTION_WEIGHTS: Dict[str, float] = {
    "travel_time": 0.40,            # Transit time from affected area
    "available_capacity": 0.35,     # Open civilian bed / floor capacity
    "utilities_resilience": 0.15,   # Verified backup power and potable water supply
    "flood_safety": 0.10,           # Distance and elevation clear of flood boundary
}

# Multi-factor weights for Route Selection
# All weights sum to 1.0
ROUTE_SELECTION_WEIGHTS: Dict[str, float] = {
    "travel_duration": 0.50,        # Estimated traversal time
    "distance": 0.25,               # Total path length in meters
    "flood_clearance": 0.25,        # Safety buffer above flood water depth threshold
}
