"""
Canonical Recommendation Pydantic Contract.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RecommendationAction(str, Enum):
    EVACUATE_ZONE = "EVACUATE_ZONE"
    REROUTE_CONVOY = "REROUTE_CONVOY"
    DISPATCH_RESCUE = "DISPATCH_RESCUE"
    DIVERT_AMBULANCES = "DIVERT_AMBULANCES"
    OPEN_SHELTER = "OPEN_SHELTER"
    PREPOSITION_RESOURCES = "PREPOSITION_RESOURCES"
    CLOSE_ROAD = "CLOSE_ROAD"


class RecommendationEntityType(str, Enum):
    ZONE = "zone"
    ROAD = "road"
    HOSPITAL = "hospital"
    SHELTER = "shelter"
    RESCUE_TEAM = "rescue_team"


class RecommendationApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class RecommendationTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_type: RecommendationEntityType
    entity_id: str
    description: str | None = None


class DecisionFactor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    weight: float
    description: str | None = None


class RecommendationUncertainty(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lower_bound: float = Field(..., ge=0.0, le=1.0)
    upper_bound: float = Field(..., ge=0.0, le=1.0)
    metric: str | None = None


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    recommendation_id: str = Field(..., min_length=3)
    created_at: datetime
    priority: int = Field(..., ge=1, le=5)
    action: RecommendationAction
    target: RecommendationTarget
    reasoning: str
    factors: list[DecisionFactor]
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    uncertainty: RecommendationUncertainty | None = None
    source_state_version: str
    requires_human_approval: Literal[True] = True
    approval_status: RecommendationApprovalStatus = RecommendationApprovalStatus.PENDING
    approved_by: str | None = None
    approved_at: datetime | None = None
