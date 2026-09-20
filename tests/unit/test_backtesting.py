"""
Unit tests for Phase 28: Historical Backtesting Engine.
"""

import pytest
from backtesting.engine import BacktestingEngine
from backtesting.historical_events import CHENNAI_2015_HISTORICAL_EVENT


def test_backtesting_engine_metrics():
    event = CHENNAI_2015_HISTORICAL_EVENT
    baseline_metrics = BacktestingEngine.evaluate_event(
        event=event,
        model_name="Phase 17 Baseline Logistic Regression",
        predicted_probs=event.baseline_predictions,
    )

    gb_metrics = BacktestingEngine.evaluate_event(
        event=event,
        model_name="Phase 18 Gradient Boosting Risk Model",
        predicted_probs=event.model_predictions,
    )

    # GB model has lower Brier score (better calibrated) and higher F1
    assert gb_metrics.brier_score < baseline_metrics.brier_score
    assert gb_metrics.f1_score >= baseline_metrics.f1_score
    assert gb_metrics.accuracy >= 0.85
    assert baseline_metrics.accuracy >= 0.70
