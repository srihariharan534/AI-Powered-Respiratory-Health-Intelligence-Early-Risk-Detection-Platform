"""
Normalization utilities for multi-factor operational recommendation scoring.
Ensures factors with disparate units (meters, seconds, beds, probabilities) are
deterministically normalized into [0.0, 1.0] before weighted aggregation.
"""

import numpy as np


def normalize_min_max(value: float, min_val: float, max_val: float, invert: bool = False) -> float:
    """
    Min-max normalization into [0.0, 1.0].
    If invert is True, lower values yield higher normalized scores (e.g. travel time, distance).
    """
    if max_val <= min_val:
        return 0.5
    clipped = float(np.clip(value, min_val, max_val))
    norm = (clipped - min_val) / (max_val - min_val)
    return 1.0 - norm if invert else norm


def normalize_severity(severity_str: str) -> float:
    """Normalizes incident severity into [0.0, 1.0]."""
    mapping = {
        "LOW": 0.20,
        "MEDIUM": 0.45,
        "HIGH": 0.75,
        "CRITICAL": 1.00,
    }
    return mapping.get(severity_str.upper(), 0.50)


def normalize_capacity(available_capacity: int, total_capacity: int) -> float:
    """Normalizes available capacity ratio into [0.0, 1.0]."""
    if total_capacity <= 0:
        return 0.0
    ratio = float(available_capacity) / float(total_capacity)
    return float(np.clip(ratio, 0.0, 1.0))
