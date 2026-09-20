"""
Exponential Backoff and Retry Classification Policy (Phase 25).
"""

import random
from typing import Set


class RetryPolicy:
    """Calculates exponential backoff delays with jitter and categorizes retryable errors."""

    def __init__(
        self,
        base_delay_ms: int = 1000,
        max_delay_ms: int = 30000,
        max_attempts: int = 5,
        jitter_ms: int = 500,
    ) -> None:
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.max_attempts = max_attempts
        self.jitter_ms = jitter_ms

        # Statuses indicating transient network or server unavailability
        self.retryable_statuses: Set[int] = {408, 429, 500, 502, 503, 504}

    def is_retryable(self, status_code: int) -> bool:
        """Determines whether an HTTP status warrants a retry."""
        return status_code in self.retryable_statuses

    def compute_delay_ms(self, attempt: int) -> int:
        """
        Computes delay: min(max_delay, base_delay * (2 ** attempt)) + random(0, jitter)
        """
        clamped_attempt = max(0, min(attempt, 10))
        exponential = self.base_delay_ms * (2 ** clamped_attempt)
        capped = min(self.max_delay_ms, exponential)
        jitter = random.randint(0, self.jitter_ms)
        return capped + jitter

    def has_exceeded_max_attempts(self, attempt: int) -> bool:
        return attempt >= self.max_attempts
