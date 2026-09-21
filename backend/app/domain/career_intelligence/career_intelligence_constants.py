"""Career Intelligence V1 — Global deterministic scoring constants.

These are compile-time module-level literals. They are NOT configurable at runtime in V1.
No environment variable, config file, or runtime override may change them.

To tune these values in a future version, update this file, increment the VERSION,
and document the change in CHANGELOG.md.

Formula:
    Score(0..100) = 100 × (
        W_F × min(1.0, frequency        / K_F) +
        W_P × min(1.0, project_count    / K_P) +
        W_E × min(1.0, experience_count / K_E) +
        W_C × min(1.0, certificate_count / K_C)
    )

Invariant (verified at module import by assertion):
    W_F + W_P + W_E + W_C == 1.0  (within float tolerance)
"""

# ---------------------------------------------------------------------------
# V1 Constants — Version tag
# ---------------------------------------------------------------------------
VERSION: str = "1.0.0"

# ---------------------------------------------------------------------------
# Scoring weights — must sum to exactly 1.0
# ---------------------------------------------------------------------------

W_E: float = 0.35  # Professional experience weight (distinct ROLE nodes via USES)
W_P: float = 0.30  # Project weight (distinct PROJECT nodes via USES)
W_C: float = 0.20  # Certificate weight (distinct CERTIFICATE nodes via CERTIFIED_IN)
W_F: float = 0.15  # Frequency weight (distinct source artifacts)

# ---------------------------------------------------------------------------
# Saturation thresholds — values at which each component reaches 1.0
# ---------------------------------------------------------------------------

K_E: int = 3  # ≥3 distinct ROLE nodes via USES → experience component = 1.0
K_P: int = 4  # ≥4 distinct PROJECT nodes    → project component = 1.0
K_C: int = 2  # ≥2 distinct CERTIFICATE nodes → certificate component = 1.0
K_F: int = 5  # ≥5 distinct source artifacts  → frequency component = 1.0

# ---------------------------------------------------------------------------
# Proficiency level thresholds (score is in [0.0, 100.0])
# ---------------------------------------------------------------------------

PROFICIENCY_BEGINNER_MAX: float = 25.0       # [0.0, 25.0)
PROFICIENCY_INTERMEDIATE_MAX: float = 55.0   # [25.0, 55.0)
PROFICIENCY_ADVANCED_MAX: float = 80.0       # [55.0, 80.0)
# EXPERT: [80.0, 100.0]

# ---------------------------------------------------------------------------
# Evidence-light definition
# A skill is evidence-light when:
#   frequency >= 1  AND  project_count == 0  AND  experience_count == 0  AND  certificate_count == 0
# ---------------------------------------------------------------------------
EVIDENCE_LIGHT_MIN_FREQUENCY: int = 1

# ---------------------------------------------------------------------------
# Module-import invariant: weights must sum to 1.0
# ---------------------------------------------------------------------------
_WEIGHT_SUM = round(W_F + W_P + W_E + W_C, 10)
assert _WEIGHT_SUM == 1.0, (
    f"Career Intelligence V1 weight invariant violated: "
    f"W_F({W_F}) + W_P({W_P}) + W_E({W_E}) + W_C({W_C}) = {_WEIGHT_SUM} ≠ 1.0"
)
