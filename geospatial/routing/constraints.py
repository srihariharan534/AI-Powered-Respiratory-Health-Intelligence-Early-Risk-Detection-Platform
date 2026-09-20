"""
Emergency Routing Constraints and Traversability Policy.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from geospatial.routing.models import VehicleType


@dataclass(frozen=True)
class EmergencyRoutingPolicy:
    """
    Policy governing how road statuses, access rules, and vehicle capabilities interact.
    """
    allow_blocked_roads: bool = False
    allow_restricted_roads: bool = True
    allow_unknown_roads: bool = True
    allow_emergency_only: bool = True
    allow_private_roads: bool = False
    max_penalty_multiplier: float = 1.0  # Optional cost penalty for restricted roads

    def evaluate_edge_traversability(
        self,
        edge_data: Dict[str, Any],
        vehicle_type: VehicleType,
    ) -> tuple[bool, Optional[str]]:
        """
        Evaluate if an edge can be traversed under this policy and vehicle type.
        Returns:
            (is_traversable, reason_if_blocked)
        """
        status = str(edge_data.get("status", "OPEN")).upper()
        accessibility = str(edge_data.get("accessibility", "ALL_VEHICLES")).upper()

        # 1. Road Status Check
        if status == "BLOCKED" and not self.allow_blocked_roads:
            return False, "Road status is BLOCKED"

        if status == "RESTRICTED" and not self.allow_restricted_roads:
            return False, "Road status is RESTRICTED and policy disallows restricted roads"

        if status == "UNKNOWN" and not self.allow_unknown_roads:
            return False, "Road status is UNKNOWN and policy disallows unknown roads"

        # 2. Accessibility Check
        if accessibility == "IMPASSABLE":
            return False, "Road accessibility is IMPASSABLE"

        if accessibility == "EMERGENCY_ONLY":
            if not self.allow_emergency_only:
                return False, "Road is EMERGENCY_ONLY but policy disallows emergency-only access"

        if accessibility == "HIGH_CLEARANCE_ONLY":
            # Fire response or heavy rescue vehicles are high clearance; standard ambulance might be restricted
            if vehicle_type == VehicleType.AMBULANCE:
                return False, "Road requires HIGH_CLEARANCE_ONLY which is unsuitable for standard ambulance"

        # 3. Private / Restricted Access tags from OSM if present
        tags = edge_data.get("tags", {})
        access_tag = tags.get("access", "").lower().strip()
        if access_tag in ("no", "private") and not self.allow_private_roads:
            # Check if emergency override exists
            emergency_tag = tags.get("emergency", "").lower().strip()
            if emergency_tag not in ("yes", "designated", "only"):
                return False, "Road access is private/no"

        return True, None
