"""
Multi-factor candidate ranker and scoring aggregator.
"""

from typing import Dict, List
from services.api.app.schemas.recommendation import DecisionFactor
from services.recommendations.contracts import ScoredCandidate


class CandidateRanker:
    """Ranks candidates by weighted multi-factor aggregate score."""

    @staticmethod
    def score_candidate(
        candidate_id: str,
        entity_type: str,
        entity_name: str,
        normalized_factors: Dict[str, float],
        weights: Dict[str, float],
        factor_descriptions: Dict[str, str],
    ) -> ScoredCandidate:
        """
        Calculates total score as dot product of normalized factor values and policy weights:
        S = sum_j (w_j * f_j)
        """
        total_score = 0.0
        factors: List[DecisionFactor] = []

        for factor_name, weight in weights.items():
            factor_val = normalized_factors.get(factor_name, 0.0)
            contrib = weight * factor_val
            total_score += contrib

            desc = factor_descriptions.get(
                factor_name,
                f"Normalized score: {factor_val:.2f} (weight: {weight:.2f})",
            )
            factors.append(
                DecisionFactor(
                    name=factor_name,
                    weight=round(weight, 4),
                    description=desc,
                )
            )

        return ScoredCandidate(
            candidate_id=candidate_id,
            entity_type=entity_type,
            entity_name=entity_name,
            total_score=round(min(1.0, max(0.0, total_score)), 4),
            hard_constraints_passed=True,
            factors=factors,
        )

    @staticmethod
    def rank(candidates: List[ScoredCandidate]) -> List[ScoredCandidate]:
        """Sorts candidates descending by total score."""
        return sorted(candidates, key=lambda c: c.total_score, reverse=True)
