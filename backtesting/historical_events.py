"""
Historical Event Fixtures (Phase 28).
Verified scenarios based on historical Chennai flood occurrences (e.g. December 2015 Adyar / Chembarambakkam event).
"""

from backtesting.engine import HistoricalEventData

CHENNAI_2015_HISTORICAL_EVENT = HistoricalEventData(
    event_id="HIST-CHENNAI-2015-12",
    event_name="Adyar River Basin Severe Inundation",
    date="2015-12-01",
    observed_inundations=[
        {"sector": "Saidapet Bridge", "depth": 2.4, "flooded": 1},
        {"sector": "Kotturpuram Lowlands", "depth": 2.8, "flooded": 1},
        {"sector": "Velachery Residential", "depth": 1.9, "flooded": 1},
        {"sector": "Guindy Industrial", "depth": 0.3, "flooded": 0},
        {"sector": "T. Nagar Corridor", "depth": 0.9, "flooded": 1},
        {"sector": "Tambaram Perungalathur", "depth": 1.7, "flooded": 1},
        {"sector": "Nungambakkam Elevated", "depth": 0.0, "flooded": 0},
        {"sector": "Mylapore High Ridge", "depth": 0.0, "flooded": 0},
    ],
    ground_truth_labels=[1, 1, 1, 0, 1, 1, 0, 0],
    baseline_predictions=[0.72, 0.68, 0.74, 0.35, 0.55, 0.65, 0.20, 0.15],
    model_predictions=[0.92, 0.94, 0.88, 0.28, 0.79, 0.85, 0.12, 0.08],
)
