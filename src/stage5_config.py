"""
Stage 5 primary scoring configuration.

All values are locked to the approved Stage 4.2 methodology.  This module
contains no data access and no side effects, so it can be imported by the
pipeline, tests and independent validators.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCORING_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "delivery_pressure_features.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "stage5"
REPORT_DIR = PROJECT_ROOT / "reports"

# ---------------------------------------------------------------------------
# Corpus and pressure-engine constants
# ---------------------------------------------------------------------------
SCORING_CORPUS_ROWS = 191_963
AUDIT_CORPUS_ROWS = 192_056
MATCH_48610_ID = 48610
MATCH_48610_CHASE_ROWS = 93
MATCH_48610_FIRST_INNINGS_ROWS = 101

PRESSURE_CUTOFF = 60.0
SHRINKAGE_K = 50.0
RAW_GATE = 75
NEFF_GATE = 35.0
MATCH_GATE = 10
RELIABILITY_GAMMA = 0.80

CRR_BASE = {"T20": 9.3201, "T20I": 8.5516}
WICKET_BASELINE = {"T20": 6.2624, "T20I": 6.7867}
GAUSSIAN_WIDTH = 12.0
BINARY_LEVERAGE = 3.0

FORMAT_LABELS = {"T20": "IPL", "T20I": "T20I"}
FORMAT_ORDER = ("T20", "T20I")

# ---------------------------------------------------------------------------
# Approved composite weights and signs
# ---------------------------------------------------------------------------
BATTER_METRICS = (
    # name, weight, raw column, N_eff column, peer-prior flag, composite sign
    ("dSR", 0.30, "dSR", "N_eff_BF", False, +1.0),
    ("SR_P", 0.25, "SR_P", "N_eff_BF", True, +1.0),
    ("Boundary_P", 0.20, "Boundary_P", "N_eff_BF", True, +1.0),
    ("dDot", 0.15, "dDot", "N_eff_legal", False, +1.0),
    ("dDR", 0.10, "dDR", "N_eff_BF", False, +1.0),
)

BOWLER_METRICS = (
    ("dEcon", 0.30, "dEcon", "N_eff_legal", False, +1.0),
    ("Econ_P", 0.25, "Econ_P", "N_eff_legal", True, -1.0),
    ("WktRate_P", 0.20, "WktRate_P", "N_eff_legal", True, +1.0),
    ("Dot_bowl_P", 0.15, "Dot_bowl_P", "N_eff_legal", True, +1.0),
    ("BoundaryConc_P", 0.10, "BoundaryConc_P", "N_eff_legal", True, -1.0),
)

# ---------------------------------------------------------------------------
# Approved post-Q9 peer means (unweighted player means)
# ---------------------------------------------------------------------------
MU_PEER = {
    ("T20", "SR_P"): 123.0195151003,
    ("T20", "Boundary_P"): 15.2429147796,
    ("T20", "Econ_P"): 11.2080294643,
    ("T20", "WktRate_P"): 0.0549119941,
    ("T20", "Dot_bowl_P"): 26.2785452045,
    ("T20", "BoundaryConc_P"): 25.8219215904,
    ("T20I", "SR_P"): 113.4018802203,
    ("T20I", "Boundary_P"): 12.9372509285,
    ("T20I", "Econ_P"): 9.6219402536,
    ("T20I", "WktRate_P"): 0.0600331371,
    ("T20I", "Dot_bowl_P"): 30.5602870144,
    ("T20I", "BoundaryConc_P"): 20.0820999300,
}

# ---------------------------------------------------------------------------
# Approved reference moments on the shrunk metric scale (population SD)
# ---------------------------------------------------------------------------
REFERENCE_MOMENTS = {
    ("batter", "T20", "dSR"): (6.9473643141, 12.7519956442),
    ("batter", "T20", "SR_P"): (143.3598182663, 16.3488265885),
    ("batter", "T20", "Boundary_P"): (18.4125015565, 3.0799490825),
    ("batter", "T20", "dDot"): (3.8392636726, 4.3995353492),
    ("batter", "T20", "dDR"): (-1.1940590841, 1.5389391176),
    ("batter", "T20I", "dSR"): (8.9481085198, 17.4810571115),
    ("batter", "T20I", "SR_P"): (132.2532442243, 16.8280446095),
    ("batter", "T20I", "Boundary_P"): (16.0055037918, 3.3359997137),
    ("batter", "T20I", "dDot"): (3.6027110473, 5.5311603837),
    ("batter", "T20I", "dDR"): (-0.9814917591, 1.6089647965),
    ("bowler", "T20", "dEcon"): (-1.0764181160, 0.9447608432),
    ("bowler", "T20", "Econ_P"): (10.5821686223, 1.0183730564),
    ("bowler", "T20", "WktRate_P"): (0.0550205061, 0.0142905047),
    ("bowler", "T20", "Dot_bowl_P"): (27.6524328950, 3.2876607418),
    ("bowler", "T20", "BoundaryConc_P"): (24.0416200626, 4.0297333498),
    ("bowler", "T20I", "dEcon"): (-1.0250545320, 0.8562377244),
    ("bowler", "T20I", "Econ_P"): (9.6816786696, 0.9079763079),
    ("bowler", "T20I", "WktRate_P"): (0.0618248276, 0.0162356787),
    ("bowler", "T20I", "Dot_bowl_P"): (30.4084257073, 3.6886061313),
    ("bowler", "T20I", "BoundaryConc_P"): (20.7606680639, 3.1488890339),
}

# ---------------------------------------------------------------------------
# Approved calibration constants
# ---------------------------------------------------------------------------
CALIBRATION = {
    "batter": {"mu": 0.1036068081, "sigma": 0.6610638828, "n": 122},
    "bowler": {"mu": 0.0256919707, "sigma": 0.6655792246, "n": 173},
}

# ---------------------------------------------------------------------------
# File names
# ---------------------------------------------------------------------------
OUTPUT_FILES = {
    "batter_format_records": "batter_format_records.csv",
    "bowler_format_records": "bowler_format_records.csv",
    "batter_scoring": "batter_scoring.csv",
    "bowler_scoring": "bowler_scoring.csv",
    "top10_batters": "top10_batters.csv",
    "top10_bowlers": "top10_bowlers.csv",
    "eligibility_audit": "eligibility_audit.csv",
    "format_eligibility_audit": "format_eligibility_audit.csv",
    "calibration_population": "calibration_population.csv",
    "scoring_validation": "stage5_scoring_validation.md",
}
