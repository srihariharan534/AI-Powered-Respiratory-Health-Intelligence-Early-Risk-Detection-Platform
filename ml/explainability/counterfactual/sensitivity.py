"""
Bounded counterfactual and sensitivity search for NEXUS risk models.
Determines minimal viable feature perturbations required to change model prediction
or cross classification thresholds, respecting strict physical constraints:
- Rainfall >= 0.0, rainfall_1h <= rainfall_24h
- Elevation >= -50.0m
- Distance to river >= 0.0m
- Slope in [0, 90] degrees
- Road density >= 0.0, infrastructure count >= 0
"""

import uuid
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from ml.explainability.contracts import (
    CounterfactualFeatureDelta,
    CounterfactualSensitivity,
)
from ml.explainability.feature_attribution.base import FEATURE_METADATA
from ml.explainability.uncertainty.bounds import PHYSICAL_FEATURE_BOUNDS
from ml.risk_model.contracts import (
    RiskFeatureRecord,
    RiskPredictionClass,
)


class CounterfactualSensitivityEngine:
    """
    Controlled counterfactual and sensitivity engine.
    Computes actionable parameter sensitivities without claiming physical causality.
    """

    def __init__(self, model: Any) -> None:
        self.model = model
        if not hasattr(model, "predict_proba"):
            raise ValueError("Model must expose predict_proba() method.")

    def find_counterfactual(
        self,
        record: RiskFeatureRecord,
        target_class: Optional[RiskPredictionClass] = None,
        threshold: float = 0.50,
    ) -> Optional[CounterfactualSensitivity]:
        """
        Determines minimal feature modifications to transition across the risk threshold.
        If record is HIGH_RISK (prob >= threshold), searches for perturbation to achieve LOW_RISK (< threshold).
        If record is LOW_RISK (prob < threshold), searches for perturbation to achieve HIGH_RISK (>= threshold).
        """
        base_df = pd.DataFrame([record.model_dump()])
        current_prob = float(self.model.predict_proba(base_df)[0])
        current_class = (
            RiskPredictionClass.HIGH_RISK
            if current_prob >= threshold
            else RiskPredictionClass.LOW_RISK
        )

        desired_class = (
            target_class
            if target_class is not None
            else (
                RiskPredictionClass.LOW_RISK
                if current_class == RiskPredictionClass.HIGH_RISK
                else RiskPredictionClass.HIGH_RISK
            )
        )

        if current_class == desired_class:
            return None  # Record already satisfies target class

        record_dict = record.model_dump()
        best_delta: Optional[CounterfactualSensitivity] = None

        # Candidate single-feature adjustments
        # To reduce risk: lower rainfall, increase elevation, increase river distance
        # To increase risk: increase rainfall, decrease elevation, decrease river distance
        is_reducing = desired_class == RiskPredictionClass.LOW_RISK

        perturbation_candidates = [
            ("rainfall_mm_24h", -0.25 if is_reducing else 0.50),
            ("elevation_m", 2.0 if is_reducing else -2.0),
            ("distance_to_river_m", 200.0 if is_reducing else -200.0),
            ("rainfall_mm_1h", -0.25 if is_reducing else 0.50),
        ]

        steps = [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0]

        for feat_name, direction in perturbation_candidates:
            orig_val = float(record_dict[feat_name])
            min_bound, max_bound = PHYSICAL_FEATURE_BOUNDS[feat_name]

            for step in steps:
                delta = direction * step * (orig_val if "rainfall" in feat_name else 1.0)
                new_val = orig_val + delta

                # Clamp within physical boundaries
                new_val = max(min_bound, min(max_bound, new_val))
                if abs(new_val - orig_val) < 1e-4:
                    continue

                # Prepare candidate dictionary
                cand_dict = dict(record_dict)
                cand_dict[feat_name] = new_val

                # Maintain rainfall consistency: 1h <= 24h
                if feat_name == "rainfall_mm_24h" and cand_dict["rainfall_mm_1h"] > new_val:
                    cand_dict["rainfall_mm_1h"] = new_val
                elif feat_name == "rainfall_mm_1h" and new_val > cand_dict["rainfall_mm_24h"]:
                    cand_dict["rainfall_mm_24h"] = new_val

                # Recompute prediction with candidate
                try:
                    cand_record = RiskFeatureRecord(**cand_dict)
                    cand_prob = float(self.model.predict_proba(pd.DataFrame([cand_record.model_dump()]))[0])
                    cand_class = (
                        RiskPredictionClass.HIGH_RISK
                        if cand_prob >= threshold
                        else RiskPredictionClass.LOW_RISK
                    )

                    if cand_class == desired_class:
                        # Found valid counterfactual
                        meta = FEATURE_METADATA.get(feat_name, {
                            "display_name": feat_name.replace("_", " ").title(),
                            "unit": "value",
                        })
                        cf_deltas = [
                            CounterfactualFeatureDelta(
                                feature_name=feat_name,
                                display_name=meta["display_name"],
                                current_value=round(orig_val, 2),
                                suggested_value=round(new_val, 2),
                                delta=round(new_val - orig_val, 2),
                                unit=meta["unit"],
                            )
                        ]
                        # If rainfall_1h also adjusted for consistency
                        if feat_name == "rainfall_mm_24h" and cand_dict["rainfall_mm_1h"] != record_dict["rainfall_mm_1h"]:
                            r1_orig = record_dict["rainfall_mm_1h"]
                            r1_new = cand_dict["rainfall_mm_1h"]
                            cf_deltas.append(
                                CounterfactualFeatureDelta(
                                    feature_name="rainfall_mm_1h",
                                    display_name="1-Hour Rainfall",
                                    current_value=round(r1_orig, 2),
                                    suggested_value=round(r1_new, 2),
                                    delta=round(r1_new - r1_orig, 2),
                                    unit="mm",
                                )
                            )

                        return CounterfactualSensitivity(
                            counterfactual_id=f"cf-{uuid.uuid4().hex[:8]}",
                            target_prediction_class=desired_class,
                            current_probability=round(current_prob, 4),
                            target_probability=round(cand_prob, 4),
                            probability_delta=round(cand_prob - current_prob, 4),
                            modified_features=cf_deltas,
                            constraints_satisfied=True,
                            method="bounded_deterministic_search",
                            limitations_note=(
                                f"Hypothetical parameter perturbation: if model input features were modified as specified, "
                                f"predicted risk probability would shift from {current_prob:.1%} to {cand_prob:.1%}. "
                                "This reflects model sensitivity and does not constitute a real-world physical or civil defense intervention."
                            ),
                        )
                except Exception:
                    continue

        return None
