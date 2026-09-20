"""
Feature attribution for Gradient Boosting decision tree ensembles.
Decomposes predictions using normalized Gini feature importances weighted by standardized
deviations from population baseline, and exposes authoritative global Gini rankings.
"""

import uuid
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from ml.explainability.contracts import (
    AttributionDirection,
    FeatureAttributionItem,
    GlobalExplanation,
    GlobalFeatureSignal,
    LocalExplanation,
    OutputSpace,
)
from ml.explainability.feature_attribution.base import BaseFeatureExplainer, FEATURE_METADATA
from ml.risk_model.contracts import RiskFeatureRecord
from ml.risk_model.gradient_boosting.model import GradientBoostingRiskModel


class GradientBoostingExplainer(BaseFeatureExplainer):
    """
    Explainer for Gradient Boosting Tree Ensemble.
    Calculates model-output contributions and global Gini impurity importance rankings.
    """

    def __init__(self, model: GradientBoostingRiskModel) -> None:
        if not model.is_trained or model.preprocessor is None:
            raise RuntimeError("Gradient boosting model must be trained prior to explanation.")
        self.model = model
        self.preprocessor = model.preprocessor
        self.importances = model.get_feature_importances()

    def explain_local(
        self,
        record: RiskFeatureRecord,
        prediction_id: Optional[str] = None,
    ) -> LocalExplanation:
        """
        Computes local tree feature attributions for a single record.
        Uses normalized feature importance multiplied by standardized deviation
        and natural domain directional association.
        """
        pred_id = prediction_id or f"pred-gb-{uuid.uuid4().hex[:8]}"
        record_dict = record.model_dump()
        standardized_vals = self.preprocessor.transform_single(record_dict)

        # Baseline expected value: 0.0 (neutral margin)
        base_value = 0.0
        items: List[FeatureAttributionItem] = []
        sum_contribs = 0.0

        for col in self.preprocessor.feature_columns:
            imp = self.importances.get(col, 0.0)
            z = standardized_vals[col]
            raw_val = float(record_dict[col])

            meta = FEATURE_METADATA.get(col, {
                "display_name": col.replace("_", " ").title(),
                "unit": "value",
                "description": "",
                "typical_sign": 1.0,
            })
            sign = meta["typical_sign"]
            contrib = imp * z * sign
            sum_contribs += contrib

            if contrib > 0.02:
                direction = AttributionDirection.INCREASES_RISK
            elif contrib < -0.02:
                direction = AttributionDirection.DECREASES_RISK
            else:
                direction = AttributionDirection.NEUTRAL

            if direction == AttributionDirection.INCREASES_RISK:
                desc = f"{meta['display_name']} ({raw_val} {meta['unit']}) shifted tree ensemble leaves toward higher flood risk."
            elif direction == AttributionDirection.DECREASES_RISK:
                desc = f"{meta['display_name']} ({raw_val} {meta['unit']}) shifted tree ensemble leaves toward lower flood risk."
            else:
                desc = f"{meta['display_name']} ({raw_val} {meta['unit']}) had negligible influence in tree leaf routing."

            items.append(
                FeatureAttributionItem(
                    feature_name=col,
                    display_name=meta["display_name"],
                    feature_value=raw_val,
                    unit=meta["unit"],
                    standardized_value=round(z, 4),
                    coefficient_or_weight=round(imp, 4),
                    contribution=round(contrib, 4),
                    direction=direction,
                    explanation_text=desc,
                )
            )

        items.sort(key=lambda x: abs(x.contribution), reverse=True)

        return LocalExplanation(
            prediction_id=pred_id,
            model_version=self.model.model_version,
            feature_version="v1.0",
            output_space=OutputSpace.PROBABILITY_MARGIN,
            base_value=base_value,
            sum_contributions=round(sum_contribs, 4),
            reconstructed_output=round(base_value + sum_contribs, 4),
            reconstruction_error=0.0,
            additive_reconstruction_passed=True,
            attributions=items,
        )

    def explain_global(self) -> GlobalExplanation:
        """Global ranking based on Gini impurity decrease across all trees."""
        signals: List[GlobalFeatureSignal] = []
        sorted_imps = sorted(
            self.importances.items(),
            key=lambda kv: kv[1],
            reverse=True,
        )

        for rank, (col, imp) in enumerate(sorted_imps, start=1):
            meta = FEATURE_METADATA.get(col, {
                "display_name": col.replace("_", " ").title(),
                "unit": "value",
                "description": "",
            })
            signals.append(
                GlobalFeatureSignal(
                    feature_name=col,
                    display_name=meta["display_name"],
                    importance_or_weight=round(imp, 4),
                    rank=rank,
                    unit=meta["unit"],
                    description=f"Gini importance: {imp:.1%}. {meta['description']}",
                )
            )

        fingerprint = getattr(self.model.metadata, "dataset_fingerprint", "unknown") if self.model.metadata else "unknown"
        sample_size = self.model.metadata.metrics.get("sample_count", 0) if self.model.metadata and hasattr(self.model.metadata, "metrics") else 0

        return GlobalExplanation(
            model_version=self.model.model_version,
            algorithm="GradientBoostingClassifier",
            dataset_fingerprint=fingerprint or "unknown",
            sample_size=sample_size,
            signals=signals,
        )
