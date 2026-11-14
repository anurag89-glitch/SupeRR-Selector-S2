"""
Stage 6 sensitivity configuration.

Every executed sensitivity is registered here with the exact parameter change
from the approved Stage 5 primary method.  Approved Stage 4.2 sensitivities and
supplementary, explicitly non-approved diagnostics are kept separate so that a
supplementary result can never be mistaken for an approved methodology scenario.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from stage5_config import (
    BINARY_LEVERAGE,
    CRR_BASE,
    GAUSSIAN_WIDTH,
    MATCH_GATE,
    NEFF_GATE,
    PRESSURE_CUTOFF,
    RAW_GATE,
    SHRINKAGE_K,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCORING_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "delivery_pressure_features.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "stage6"
REPORT_PATH = PROJECT_ROOT / "reports" / "stage6_sensitivity_report.md"

# Approved Stage 4.2 first-innings comparison CRR values (Appendix A.1, item 2).
CRR_FIRST_INNINGS = {"T20": 9.3749, "T20I": 8.6673}

# Stage 4.2 publishes alternative reference moments for the two metric
# definition sensitivities below (Section 8.5 runs proxy; Section 8.7
# Definition B dismissal rate).  Every other scenario holds reference moments,
# peer means and calibration constants at the approved primary values so that
# the comparison isolates the stated parameter change.
SENSITIVITY_REFERENCE_MOMENTS = {
    "DISMISSAL_RATE_WIDE_EXCLUDED": {
        ("batter", "T20", "dDR"): (-1.159482, 1.503531),
        ("batter", "T20I", "dDR"): (-0.971921, 1.613094),
    },
    "BOUNDARY_RUNS_PROXY": {
        ("batter", "T20", "Boundary_P"): (18.421896, 3.080243),
        ("batter", "T20I", "Boundary_P"): (16.017383, 3.339804),
    },
}

# Sensitivity values expressly requested for supplementary bowling diagnostics.
SUPPLEMENTARY_SIGMA_VALUES = (8.0, 10.0, 15.0, 20.0)
SUPPLEMENTARY_H_MODES = ("linear", "quadratic")
SUPPLEMENTARY_LEVERAGE_VALUES = (0.0, 1.5, 5.0)


@dataclass(frozen=True)
class Scenario:
    """One registered Stage 6 sensitivity scenario."""

    scenario_id: str
    category: str
    status: str
    approved: bool
    mandatory: bool
    description: str
    change_from_primary: str
    pressure_cutoff: float = PRESSURE_CUTOFF
    shrinkage_k: float = SHRINKAGE_K
    raw_gate: int = RAW_GATE
    neff_gate: float = NEFF_GATE
    match_gate: int = MATCH_GATE
    sigma: float = GAUSSIAN_WIDTH
    leverage: float = BINARY_LEVERAGE
    h_mode: str = "sqrt"
    crr_source: str = "all_innings"
    include_48610_chase: bool = False
    dismissal_definition: str = "A"
    boundary_source: str = "flags"
    boundary_legality: str = "all"
    other_as_legal: bool = False
    wicket_neff: str = "legal"
    neff_scope: str = "primary"
    wide_stump_action: str = "retain"
    cross_format_weight: str = "equal"
    eligibility: str = "primary"
    season_weight: str = "delivery"
    season_from: int | None = None
    blocked_reason: str = ""

    def parameter_text(self) -> str:
        """Compact human-readable parameter fingerprint."""
        parts = [
            f"P={self.pressure_cutoff:g}",
            f"K={self.shrinkage_k:g}",
            f"N_raw>={self.raw_gate}",
            f"N_eff>={self.neff_gate:g}",
            f"M>={self.match_gate}",
            f"sigma={self.sigma:g}",
            f"leverage={self.leverage:g}",
            f"h={self.h_mode}",
            f"CRR={self.crr_source}",
            f"48610={'included_P1' if self.include_48610_chase else 'excluded'}",
            f"dismissal={self.dismissal_definition}",
            f"boundary={self.boundary_source}",
            f"boundary_legality={self.boundary_legality}",
            f"other_as_legal={self.other_as_legal}",
            f"wkt_neff={self.wicket_neff}",
            f"neff_scope={self.neff_scope}",
            f"wide_stump={self.wide_stump_action}",
            f"format_weight={self.cross_format_weight}",
            f"eligibility={self.eligibility}",
            f"season_weight={self.season_weight}",
            f"season_from={self.season_from}",
        ]
        return "; ".join(parts)


def _s(
    scenario_id: str,
    category: str,
    description: str,
    change_from_primary: str,
    **kwargs,
) -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        category=category,
        status="COMPLETED",
        approved=True,
        mandatory=True,
        description=description,
        change_from_primary=change_from_primary,
        **kwargs,
    )


def _supp(
    scenario_id: str,
    description: str,
    change_from_primary: str,
    **kwargs,
) -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        category="supplementary_non_approved",
        status="COMPLETED_SUPPLEMENTARY",
        approved=False,
        mandatory=False,
        description=description,
        change_from_primary=change_from_primary,
        **kwargs,
    )


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        scenario_id="PRIMARY",
        category="baseline",
        status="PRIMARY",
        approved=True,
        mandatory=True,
        description="Approved Stage 5 primary ranking (reference baseline).",
        change_from_primary="None.",
    ),
    # ------------------------------------------------------------------
    # Stage 4.2 Section 13.1 approved sensitivity grid
    # ------------------------------------------------------------------
    _s(
        "P_55",
        "approved_grid",
        "Pressure cutoff P=55 instead of P=60.",
        "pressure_cutoff 60 -> 55; all other parameters primary.",
        pressure_cutoff=55.0,
    ),
    _s(
        "P_65",
        "approved_grid",
        "Pressure cutoff P=65 instead of P=60.",
        "pressure_cutoff 60 -> 65; all other parameters primary.",
        pressure_cutoff=65.0,
    ),
    _s(
        "K_25",
        "approved_grid",
        "Shrinkage constant K=25 instead of K=50.",
        "shrinkage_k 50 -> 25; all other parameters primary.",
        shrinkage_k=25.0,
    ),
    _s(
        "K_100",
        "approved_grid",
        "Shrinkage constant K=100 instead of K=50.",
        "shrinkage_k 50 -> 100; all other parameters primary.",
        shrinkage_k=100.0,
    ),
    _s(
        "NRAW_50",
        "approved_grid",
        "Raw pressure-delivery gate N_raw>=50 instead of >=75.",
        "raw_gate 75 -> 50; all other parameters primary.",
        raw_gate=50,
    ),
    _s(
        "NRAW_100",
        "approved_grid",
        "Raw pressure-delivery gate N_raw>=100 instead of >=75.",
        "raw_gate 75 -> 100; all other parameters primary.",
        raw_gate=100,
    ),
    # ------------------------------------------------------------------
    # Stage 4.2 Section 13.2 mandatory analyses
    # ------------------------------------------------------------------
    _s(
        "WKT_RATE_NEFF_ALL_DELIVERIES",
        "approved_mandatory",
        "Wicket-rate N_eff definition B: all-delivery instead of legal-delivery-only.",
        "WktRate_P shrinkage N_eff uses N_eff_del instead of N_eff_legal; metric denominator and wide stumpings unchanged.",
        wicket_neff="all_deliveries",
    ),
    _s(
        "DISMISSAL_RATE_WIDE_EXCLUDED",
        "approved_mandatory",
        "Batter dismissal-rate definition B: wide-delivery dismissals excluded from numerator.",
        "D removes striker dismissals on wide deliveries from the pressure numerator; balls-faced denominator unchanged and personal baseline held at Definition A. Uses the Section 8.7 Definition B reference moments.",
        dismissal_definition="B",
    ),
    _s(
        "BOUNDARY_RUNS_PROXY",
        "approved_mandatory",
        "Batter boundary percentage uses batter_runs in {4,6} instead of source flags.",
        "Batter boundary numerator flags -> batter_runs proxy; bowler boundary-conceded retains source flags. Uses the Section 8.5 runs-proxy reference moments.",
        boundary_source="runs",
    ),
    _s(
        "OTHER_BOUNDARY_LEGAL_OVERSTEP",
        "approved_mandatory",
        "Bowler boundary-conceded verified core: legal + overstep deliveries only.",
        "boundary_legality all -> legal_overstep; excludes 26 other-delivery boundaries at P_bowl>=60 (9,816 -> 9,790).",
        boundary_legality="legal_overstep",
    ),
    _s(
        "OTHER_BOUNDARY_LEGAL_ONLY",
        "approved_mandatory",
        "Bowler boundary-conceded legal-only rule.",
        "boundary_legality all -> legal; excludes 26 other and 34 overstep boundaries at P_bowl>=60 (9,816 -> 9,756).",
        boundary_legality="legal",
    ),
    _s(
        "OTHER_AS_LEGAL",
        "approved_mandatory",
        "`other` extras treated as legal for economy and dot-ball denominators.",
        "other_as_legal True; 256 other deliveries become legal; runs and bowler charges unchanged.",
        other_as_legal=True,
    ),
    _s(
        "FORMAT_WEIGHT_NEFF_PROPORTIONAL",
        "approved_mandatory",
        "Cross-format composite weighted by N_eff_del instead of equal format weights.",
        "player Z_comp = sum(N_eff_del_f * Z_f) / sum(N_eff_del_f); equal weighting remains primary.",
        cross_format_weight="neff",
    ),
    _s(
        "CRR_FIRST_INNINGS",
        "approved_mandatory",
        "CRR baseline uses first-innings comparison values instead of all-innings pooled values.",
        "CRR T20 9.3201 -> 9.3749 and T20I 8.5516 -> 8.6673; wicket baseline unchanged.",
        crr_source="first_innings",
    ),
    _s(
        "ELIG_M_ALL",
        "approved_mandatory",
        "Final match-breadth gate uses M_all>=10 instead of M_role>=10.",
        "ranking gate M_role>=10 -> M_all>=10; F_non-empty unchanged.",
        eligibility="m_all",
    ),
    _s(
        "ELIG_PER_FORMAT_M10",
        "approved_mandatory",
        "Match-breadth gate applied per format: every format in F must have M_format>=10.",
        "format gate adds M_format>=10; final M_role>=10 gate unchanged.",
        eligibility="per_format_m10",
    ),
    _s(
        "NEFF_SCOPE_ALL_DELIVERIES",
        "approved_mandatory",
        "All bowler metric shrinkage uses all-delivery N_eff where the metric permits.",
        "N_eff_legal -> N_eff_del for all five bowler metrics; metric raw denominators unchanged.",
        neff_scope="all_deliveries",
    ),
    _s(
        "MATCH_48610_P1_FALLBACK",
        "approved_mandatory",
        "Match 48610 93 chase rows included under explicitly labelled P1 fallback.",
        "Include 192,056 audit rows and evaluate unresolved chase with P1 equations; primary still excludes the 93 rows.",
        include_48610_chase=True,
    ),
    _s(
        "SEASON_EQUAL",
        "approved_mandatory",
        "Season-equal weighting: each format-season contributes equal total pressure weight.",
        "pressure weights divided by format-season weight total; delivery-level pooling remains primary.",
        season_weight="equal",
    ),
    _s(
        "SEASON_2024_2026",
        "approved_mandatory",
        "Restrict corpus to seasons starting in 2024-2026.",
        "season_from 2024; 2022, 2022/23, 2023 and 2023/24 deliveries excluded.",
        season_from=2024,
    ),
    # ------------------------------------------------------------------
    # User-requested supplementary diagnostics (not approved by Stage 4.2)
    # ------------------------------------------------------------------
    _supp(
        "SUPP_SIGMA_8",
        "Supplementary: bowling Gaussian width sigma_S=8 runs.",
        "sigma 12 -> 8; not an approved Stage 4.2 parameterization.",
        sigma=8.0,
    ),
    _supp(
        "SUPP_SIGMA_10",
        "Supplementary: bowling Gaussian width sigma_S=10 runs.",
        "sigma 12 -> 10; not an approved Stage 4.2 parameterization.",
        sigma=10.0,
    ),
    _supp(
        "SUPP_SIGMA_15",
        "Supplementary: bowling Gaussian width sigma_S=15 runs.",
        "sigma 12 -> 15; not an approved Stage 4.2 parameterization.",
        sigma=15.0,
    ),
    _supp(
        "SUPP_SIGMA_20",
        "Supplementary: bowling Gaussian width sigma_S=20 runs.",
        "sigma 12 -> 20; not an approved Stage 4.2 parameterization.",
        sigma=20.0,
    ),
    _supp(
        "SUPP_H_LINEAR",
        "Supplementary: wicket-remaining resource depth h = W_rem/10 (linear).",
        "h sqrt(W_rem/10) -> W_rem/10; not an approved Stage 4.2 parameterization.",
        h_mode="linear",
    ),
    _supp(
        "SUPP_H_QUADRATIC",
        "Supplementary: wicket-remaining resource depth h = (W_rem/10)^2 (quadratic).",
        "h sqrt(W_rem/10) -> (W_rem/10)^2; not an approved Stage 4.2 parameterization.",
        h_mode="quadratic",
    ),
    _supp(
        "SUPP_LEVERAGE_0",
        "Supplementary: binary finish leverage disabled (0.00).",
        "leverage 3.00 -> 0.00; trigger unchanged; not an approved Stage 4.2 parameterization.",
        leverage=0.0,
    ),
    _supp(
        "SUPP_LEVERAGE_1_5",
        "Supplementary: binary finish leverage 1.50.",
        "leverage 3.00 -> 1.50; trigger unchanged; not an approved Stage 4.2 parameterization.",
        leverage=1.5,
    ),
    _supp(
        "SUPP_LEVERAGE_5",
        "Supplementary: binary finish leverage 5.00.",
        "leverage 3.00 -> 5.00; trigger unchanged; not an approved Stage 4.2 parameterization.",
        leverage=5.0,
    ),
    _supp(
        "SUPP_WIDE_STUMP_REMOVED",
        "Supplementary: wide-delivery stumpings removed from bowler wicket numerator.",
        "25 wide stumpings (6 in bowler pressure set) removed from WktRate_P numerator; not an approved Stage 4.2 parameterization.",
        wide_stump_action="remove",
    ),
    # ------------------------------------------------------------------
    # Explicitly blocked / not-run scenarios
    # ------------------------------------------------------------------
    Scenario(
        scenario_id="OPTIONAL_NEFF_CAPPED",
        category="optional",
        status="OPTIONAL_NOT_RUN",
        approved=False,
        mandatory=False,
        description="Capped N_eff-proportional cross-format weighting.",
        change_from_primary="Not run.",
        cross_format_weight="neff_capped",
        blocked_reason=(
            "No numeric cap C is registered in Stage 4.2. The methodology states C "
            "is required only if this optional sensitivity is performed."
        ),
    ),
    Scenario(
        scenario_id="BASELINE_EXPOSURE_ALT",
        category="blocked",
        status="BLOCKED_NOT_APPROVED",
        approved=False,
        mandatory=False,
        description="Alternative baseline exposure threshold.",
        change_from_primary="Not run.",
        blocked_reason=(
            "Stage 4.2 requires any alternative to the 120-ball baseline exposure "
            "rule to be pre-registered before execution. No alternative is registered."
        ),
    ),
)


SCENARIO_BY_ID = {s.scenario_id: s for s in SCENARIOS}
COMPLETED_SCENARIOS = tuple(
    s for s in SCENARIOS if s.status in {"PRIMARY", "COMPLETED", "COMPLETED_SUPPLEMENTARY"}
)
MANDATORY_SCENARIOS = tuple(s for s in SCENARIOS if s.mandatory)

OUTPUT_FILES = {
    "sensitivity_summary": "sensitivity_summary.csv",
    "batter_sensitivity_rankings": "batter_sensitivity_rankings.csv",
    "bowler_sensitivity_rankings": "bowler_sensitivity_rankings.csv",
    "batter_top10_stability": "batter_top10_stability.csv",
    "bowler_top10_stability": "bowler_top10_stability.csv",
    "eligibility_sensitivity": "eligibility_sensitivity.csv",
    "player_rank_changes": "player_rank_changes.csv",
    "validation_checks": "stage6_validation_checks.csv",
}
