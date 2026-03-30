"""Predefined consent-distribution scenarios for impact simulation.

Each scenario maps consent levels (full / analytics_only / minimal) to
their expected proportion of the total customer population.  Proportions
must sum to 1.0.
"""

from __future__ import annotations

from typing import Final

ConsentDistribution = dict[str, float]
"""Mapping of consent_level -> population proportion (sums to 1.0)."""

CONSENT_LEVELS: Final[list[str]] = ["full", "analytics_only", "minimal"]

SCENARIOS: Final[dict[str, ConsentDistribution]] = {
    "current_state": {
        "full": 0.42,
        "analytics_only": 0.28,
        "minimal": 0.30,
    },
    "privacy_first_eu": {
        "full": 0.25,
        "analytics_only": 0.25,
        "minimal": 0.50,
    },
    "post_cookie_apocalypse": {
        "full": 0.15,
        "analytics_only": 0.20,
        "minimal": 0.65,
    },
    "best_case_ux": {
        "full": 0.60,
        "analytics_only": 0.25,
        "minimal": 0.15,
    },
    "german_strict": {
        "full": 0.20,
        "analytics_only": 0.30,
        "minimal": 0.50,
    },
}


def validate_distribution(dist: ConsentDistribution) -> None:
    """Raise ``ValueError`` if *dist* is not a valid consent distribution.

    Args:
        dist: Mapping of consent_level to proportion.

    Raises:
        ValueError: If keys don't match expected levels or proportions
            don't sum to 1.0 (within tolerance 1e-6).
    """
    missing = set(CONSENT_LEVELS) - set(dist)
    if missing:
        raise ValueError(f"Missing consent levels: {missing}")
    total = sum(dist.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Proportions must sum to 1.0, got {total:.6f}")
