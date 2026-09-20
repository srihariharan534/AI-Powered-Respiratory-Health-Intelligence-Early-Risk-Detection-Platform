"""
Resource Allocation Package (Feature C).
"""

from services.recommendations.resource_allocation.optimizer import (
    AllocationProposal,
    AvailableResource,
    ResourceAllocationOptimizer,
    ResourceAllocationResult,
    SectorRequirement,
)

__all__ = [
    "ResourceAllocationOptimizer",
    "SectorRequirement",
    "AvailableResource",
    "AllocationProposal",
    "ResourceAllocationResult",
]
