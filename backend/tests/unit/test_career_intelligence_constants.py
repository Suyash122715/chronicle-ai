"""Unit tests for Career Intelligence V1 scoring constants."""

import math
from app.domain.career_intelligence.career_intelligence_constants import (
    EVIDENCE_LIGHT_MIN_FREQUENCY,
    K_C,
    K_E,
    K_F,
    K_P,
    W_C,
    W_E,
    W_F,
    W_P,
)


def test_weights_sum_to_one_point_zero() -> None:
    """Verifies that W_F + W_P + W_E + W_C == 1.00 exactly."""
    total = W_F + W_P + W_E + W_C
    assert math.isclose(total, 1.0, rel_tol=1e-9), f"Weights must sum to 1.0, got {total}"
    assert total == 1.0, f"Weights float sum is {total}"


def test_individual_weight_values() -> None:
    """Verifies individual weight values as defined in V1 specifications."""
    assert W_E == 0.35, "Experience weight W_E must be 0.35"
    assert W_P == 0.30, "Project weight W_P must be 0.30"
    assert W_C == 0.20, "Certificate weight W_C must be 0.20"
    assert W_F == 0.15, "Frequency weight W_F must be 0.15"


def test_saturation_thresholds_are_positive_integers() -> None:
    """Verifies that all saturation constants Kx are positive integers."""
    for name, val in [("K_F", K_F), ("K_P", K_P), ("K_E", K_E), ("K_C", K_C)]:
        assert isinstance(val, int), f"{name} must be an integer, got {type(val)}"
        assert val > 0, f"{name} must be positive, got {val}"

    assert K_F == 5
    assert K_P == 4
    assert K_E == 3
    assert K_C == 2


def test_evidence_light_constant() -> None:
    """Verifies EVIDENCE_LIGHT_MIN_FREQUENCY is 1."""
    assert EVIDENCE_LIGHT_MIN_FREQUENCY == 1
