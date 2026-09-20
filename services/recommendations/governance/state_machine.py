"""
Centralized Recommendation State Machine (Phase 21).
Validates lifecycle transitions and rejects invalid state mutations.
"""

from typing import Dict, Set
from services.api.app.schemas.recommendation import (
    Recommendation,
    RecommendationApprovalStatus,
)


class GovernanceError(Exception):
    """Base exception for recommendation governance failures."""
    pass


class InvalidStateTransitionError(GovernanceError):
    """Raised when an invalid state transition is requested."""
    pass


class StaleRecommendationError(GovernanceError):
    """Raised when an approval is attempted on a stale recommendation."""
    pass


class UnauthorizedActionError(GovernanceError):
    """Raised when the actor lacks permission for the requested action."""
    pass


class PreconditionFailedError(GovernanceError):
    """Raised when an operational precondition fails (e.g. facility full, incident resolved)."""
    pass


class RecommendationStateMachine:
    """
    Central authority governing recommendation status transitions.
    Canonical valid transitions:
        PENDING -> APPROVED
        PENDING -> REJECTED
        PENDING -> EXPIRED
    All other transitions are forbidden.
    """

    ALLOWED_TRANSITIONS: Dict[RecommendationApprovalStatus, Set[RecommendationApprovalStatus]] = {
        RecommendationApprovalStatus.PENDING: {
            RecommendationApprovalStatus.APPROVED,
            RecommendationApprovalStatus.REJECTED,
            RecommendationApprovalStatus.EXPIRED,
        },
        RecommendationApprovalStatus.APPROVED: set(),  # Terminal
        RecommendationApprovalStatus.REJECTED: set(),  # Terminal
        RecommendationApprovalStatus.EXPIRED: set(),   # Terminal
    }

    @classmethod
    def can_transition(
        cls,
        current_status: RecommendationApprovalStatus,
        target_status: RecommendationApprovalStatus,
    ) -> bool:
        """Checks whether the requested transition is theoretically allowed."""
        return target_status in cls.ALLOWED_TRANSITIONS.get(current_status, set())

    @classmethod
    def validate_transition(
        cls,
        recommendation: Recommendation,
        target_status: RecommendationApprovalStatus,
    ) -> None:
        """
        Validates the proposed transition against current recommendation state.
        Raises InvalidStateTransitionError if the transition is prohibited.
        """
        current_status = recommendation.approval_status

        if current_status == target_status:
            raise InvalidStateTransitionError(
                f"Recommendation '{recommendation.recommendation_id}' is already in status '{current_status.value}'."
            )

        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise InvalidStateTransitionError(
                f"Invalid transition for recommendation '{recommendation.recommendation_id}': "
                f"'{current_status.value}' -> '{target_status.value}'. "
                f"Allowed target states: {[s.value for s in allowed]}"
            )
