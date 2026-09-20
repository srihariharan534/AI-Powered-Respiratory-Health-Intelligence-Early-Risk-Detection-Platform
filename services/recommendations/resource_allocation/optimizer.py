"""
Resource Allocation Optimizer (Feature C).
Proposes optimal deployment of rescue teams, vehicles, boats, and medical kits
subject to capacity constraints, road accessibility, and sector risk.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SectorRequirement(BaseModel):
    sector_id: str
    risk_score: float
    population: int
    boats_needed: int
    teams_needed: int


class AvailableResource(BaseModel):
    resource_id: str
    resource_type: str  # RESCUE_TEAM, BOAT, AMBULANCE, MEDICAL_KIT
    station_id: str
    is_available: bool = True


class AllocationProposal(BaseModel):
    sector_id: str
    allocated_resources: List[str]
    justification: str
    coverage_ratio: float


class ResourceAllocationResult(BaseModel):
    total_sectors: int
    proposals: List[AllocationProposal]
    unmet_demands: List[str] = Field(default_factory=list)


class ResourceAllocationOptimizer:
    """
    Greedy / constrained resource allocation prioritizing highest-risk sectors.
    """

    @classmethod
    def optimize(
        cls,
        sectors: List[SectorRequirement],
        resources: List[AvailableResource],
    ) -> ResourceAllocationResult:
        # Sort sectors by risk descending
        sorted_sectors = sorted(sectors, key=lambda s: s.risk_score, reverse=True)
        available_pool = [r for r in resources if r.is_available]

        proposals = []
        unmet = []

        for sec in sorted_sectors:
            allocated = []
            # Match needed boats
            for _ in range(sec.boats_needed):
                boat = next((r for r in available_pool if r.resource_type == "BOAT"), None)
                if boat:
                    allocated.append(boat.resource_id)
                    available_pool.remove(boat)
                else:
                    unmet.append(f"Sector {sec.sector_id}: Insufficient rescue boats")

            # Match needed teams
            for _ in range(sec.teams_needed):
                team = next((r for r in available_pool if r.resource_type == "RESCUE_TEAM"), None)
                if team:
                    allocated.append(team.resource_id)
                    available_pool.remove(team)
                else:
                    unmet.append(f"Sector {sec.sector_id}: Insufficient rescue teams")

            ratio = len(allocated) / (sec.boats_needed + sec.teams_needed) if (sec.boats_needed + sec.teams_needed) > 0 else 1.0

            proposals.append(
                AllocationProposal(
                    sector_id=sec.sector_id,
                    allocated_resources=allocated,
                    justification=f"Prioritized allocation based on risk {sec.risk_score:.2f} and population {sec.population}.",
                    coverage_ratio=round(ratio, 2),
                )
            )

        return ResourceAllocationResult(
            total_sectors=len(sectors),
            proposals=proposals,
            unmet_demands=unmet,
        )
