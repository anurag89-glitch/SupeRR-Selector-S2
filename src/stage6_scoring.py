"""
Stage 6 parameterized scoring engine.

The engine reproduces the approved Stage 5 primary pipeline exactly when the
PRIMARY scenario is selected, and varies only the registered Stage 6
parameters.  Reference moments, peer means and calibration constants are held
fixed at their approved primary values so that a sensitivity isolates the
effect of the stated parameter change.

No raw or approved pressure-feature dataset is written by this module.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from stage5_config import (
    AUDIT_CORPUS_ROWS,
    BATTER_METRICS,
    BOWLER_METRICS,
    CALIBRATION,
    CRR_BASE,
    FORMAT_LABELS,
    FORMAT_ORDER,
    MATCH_48610_ID,
    MU_PEER,
    RELIABILITY_GAMMA,
    SCORING_CORPUS_ROWS,
    SCORING_DATA_PATH,
    REFERENCE_MOMENTS,
    WICKET_BASELINE,
)
from stage6_config import (
    CRR_FIRST_INNINGS,
    SENSITIVITY_REFERENCE_MOMENTS,
    Scenario,
)

READ_COLUMNS = [
    "match_id", "innings", "season", "match_format", "match_status_category",
    "is_super_over", "striker_id", "striker_name", "bowler_id", "bowler_name",
    "max_balls", "legal_balls_before", "runs_before", "wickets_before",
    "runs_required", "target_provenance", "is_target_reached_before",
    "batter_runs", "extras_runs", "extras_type_clean",
    "is_legal_delivery", "is_dot_ball", "is_four", "is_six",
    "is_wicket", "dismissed_player_id", "dismissal_type_clean",
    "is_bowler_wicket",
]

STATUS_RANKING = "RANKING_ELIGIBLE"
STATUS_M_BREADTH = "M_BREADTH_INSUFFICIENT"
STATUS_BASELINE = "BASELINE_INSUFFICIENT"
STATUS_SAMPLE = "INSUFFICIENT_SAMPLE"


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------
def load_stage6_corpus(path=SCORING_DATA_PATH) -> pd.DataFrame:
    """Load the 192,056-row completed non-Super-Over audit corpus once."""
    df = pd.read_csv(path, usecols=READ_COLUMNS, low_memory=False)
    df = df[
        (df["match_status_category"] == "COMPLETED")
        & (~df["is_super_over"].astype(bool))
    ].copy()
    max_balls = pd.to_numeric(df["max_balls"], errors="coerce")
    legal_before = pd.to_numeric(df["legal_balls_before"], errors="coerce")
    df = df[(max_balls > 0) & ((max_balls - legal_before) > 0)].copy()
    if len(df) != AUDIT_CORPUS_ROWS:
        raise ValueError(
            f"Expected {AUDIT_CORPUS_ROWS:,} completed non-Super-Over rows, "
            f"found {len(df):,}."
        )
    return df


def _season_start_year(season: pd.Series) -> pd.Series:
    extracted = season.astype(str).str.extract(r"^(\d{4})", expand=False)
    return pd.to_numeric(extracted, errors="coerce")


def _scenario_corpus(base: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
    """Apply season restriction and the primary/fallback Match 48610 rule."""
    df = base
    if scenario.season_from is not None:
        years = _season_start_year(df["season"])
        df = df[years >= scenario.season_from].copy()
    if not scenario.include_48610_chase:
        df = df[
            ~((df["match_id"] == MATCH_48610_ID) & (df["innings"] == 2))
        ].copy()
    return df


# ---------------------------------------------------------------------------
# Pressure engine
# ---------------------------------------------------------------------------
def _sigmoid(z):
    return 100.0 / (1.0 + np.exp(-z))


def _h_resource(w_rem: np.ndarray, mode: str) -> np.ndarray:
    ratio = w_rem / 10.0
    if mode == "sqrt":
        return np.sqrt(ratio)
    if mode == "linear":
        return ratio
    if mode == "quadratic":
        return np.square(ratio)
    raise ValueError(f"Unknown h mode: {mode}")


def compute_pressure_features_param(
    df: pd.DataFrame, scenario: Scenario, unresolved_fallback: bool = False
) -> pd.DataFrame:
    """Compute P_bat, P_bowl and pressure weights under one scenario."""
    out = df.copy()
    b = out["legal_balls_before"].astype(float).to_numpy()
    mb = out["max_balls"].astype(float).to_numpy()
    balls_rem = mb - b
    runs_before = out["runs_before"].astype(float).to_numpy()
    wickets_before = out["wickets_before"].astype(float).to_numpy()
    runs_req = out["runs_required"].astype(float).to_numpy()
    is_t20 = (out["match_format"] == "T20").to_numpy()

    crr_map = CRR_BASE if scenario.crr_source == "all_innings" else CRR_FIRST_INNINGS
    crr = np.where(is_t20, crr_map["T20"], crr_map["T20I"])
    wicket_base = np.where(
        is_t20, WICKET_BASELINE["T20"], WICKET_BASELINE["T20I"]
    )

    # First innings (P1), unchanged from Stage 5.
    expected_runs = crr * b / 6.0
    expected_wickets = wicket_base * (mb / 120.0) * np.power(b / mb, 0.85)
    s_runs = np.tanh((expected_runs - runs_before) / 15.0)
    s_wickets = np.clip(wickets_before / (expected_wickets + 0.50), 0.0, 3.0) / 3.0
    w_stab = b / (b + 12.0)
    u_phase = np.power(b / mb, 1.50)

    z_bat1 = 2.20 * s_wickets + 1.80 * (w_stab * s_runs) + 1.50 * u_phase - 1.50
    z_bowl1 = 2.00 * (-s_runs) + 1.50 * (1.0 - s_wickets) + 1.80 * u_phase - 1.80
    p_bat1 = _sigmoid(z_bat1)
    p_bowl1 = _sigmoid(z_bowl1)

    # Second innings (P2), with parameterized sigma, leverage and h.
    w_rem = 10.0 - wickets_before
    rrr = np.divide(
        6.0 * runs_req,
        balls_rem,
        out=np.full_like(runs_req, np.nan, dtype=float),
        where=balls_rem > 0,
    )
    theta = rrr / crr
    demand = theta * np.power(10.0 / (w_rem + 1.0), 0.60)
    time_decay = np.power(b / mb, 0.75)
    z_bat2 = 2.50 * np.log(np.maximum(0.10, demand)) + 1.80 * time_decay - 1.20

    h = _h_resource(w_rem, scenario.h_mode)
    expected_runs_bowl = crr * (balls_rem / 6.0) * h
    surplus = expected_runs_bowl - runs_req
    c_match = np.exp(-(surplus ** 2) / (2.0 * scenario.sigma ** 2))
    core = 5.50 * (0.65 + 0.35 * h) + 1.20 * time_decay
    leverage = np.where(
        (balls_rem <= 12) & (runs_req > 0) & (runs_req <= 12) & (w_rem == 1),
        scenario.leverage,
        0.0,
    )
    z_bowl2 = c_match * core + leverage - 4.20
    p_bat2 = _sigmoid(z_bat2)
    p_bowl2 = _sigmoid(z_bowl2)

    second = out["innings"].to_numpy() == 2
    resolved_target = out["target_provenance"].isin(
        ["STANDARD_TARGET", "VERIFIED_REVISED_TARGET"]
    ).to_numpy()
    target_reached = out["is_target_reached_before"].fillna(False).to_numpy()
    chase = (
        second
        & resolved_target
        & np.isfinite(runs_req)
        & (balls_rem > 0)
        & (~target_reached)
    )
    invalid_second = second & (~chase)

    p_bat = np.where(chase, p_bat2, p_bat1)
    p_bowl = np.where(chase, p_bowl2, p_bowl1)
    if unresolved_fallback:
        p_bat = np.where(invalid_second, p_bat1, p_bat)
        p_bowl = np.where(invalid_second, p_bowl1, p_bowl)
    else:
        p_bat = np.where(invalid_second, np.nan, p_bat)
        p_bowl = np.where(invalid_second, np.nan, p_bowl)

    out["balls_remaining_calc"] = balls_rem
    out["p_bat"] = p_bat
    out["p_bowl"] = p_bowl
    out["pressure_basis"] = np.select(
        [invalid_second & unresolved_fallback, invalid_second, chase, second],
        ["P1_FALLBACK_SENSITIVITY", "EXCLUDED", "P2_CHASE", "P2_CHASE"],
        default="P1_FIRST_INNINGS",
    )
    out["w_bat"] = np.where(
        np.isfinite(p_bat) & (p_bat >= scenario.pressure_cutoff),
        np.square(p_bat / 100.0),
        0.0,
    )
    out["w_bowl"] = np.where(
        np.isfinite(p_bowl) & (p_bowl >= scenario.pressure_cutoff),
        np.square(p_bowl / 100.0),
        0.0,
    )
    return out


# ---------------------------------------------------------------------------
# Delivery attribution
# ---------------------------------------------------------------------------
def add_delivery_metrics_param(df: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
    """Add scenario-specific delivery attribution fields."""
    out = df.copy()
    extras = out["extras_type_clean"].fillna("none")
    legal_raw = out["is_legal_delivery"].fillna(False).astype(bool)

    out["BF"] = (extras != "wide").astype(float)
    legal = legal_raw.copy()
    if scenario.other_as_legal:
        legal = legal | (extras == "other")
    out["legal"] = legal.astype(float)

    dot_raw = out["is_dot_ball"].fillna(False).astype(bool)
    if scenario.other_as_legal:
        other_zero = (extras == "other") & (
            (out["batter_runs"].astype(float) + out["extras_runs"].astype(float)) == 0
        )
        dot = np.where(extras == "other", other_zero, dot_raw)
        out["dot_i"] = dot.astype(float)
    else:
        out["dot_i"] = dot_raw.astype(float)

    flags = out["is_four"].fillna(False) | out["is_six"].fillna(False)
    if scenario.boundary_source == "runs":
        boundary_batter = out["batter_runs"].isin([4, 6])
    elif scenario.boundary_source == "flags":
        boundary_batter = flags
    else:
        raise ValueError(f"Unknown boundary source: {scenario.boundary_source}")
    out["boundary_batter"] = boundary_batter.astype(float)

    if scenario.boundary_legality == "all":
        allowed = pd.Series(True, index=out.index)
    elif scenario.boundary_legality == "legal_overstep":
        allowed = legal_raw | (extras == "overstep")
    elif scenario.boundary_legality == "legal":
        allowed = legal_raw
    else:
        raise ValueError(
            f"Unknown boundary legality: {scenario.boundary_legality}"
        )
    # The approved runs-proxy sensitivity applies to the batter boundary
    # percentage only; bowler boundary-conceded always uses the source flags.
    out["boundary_bowler"] = (flags & allowed).astype(float)

    striker_dismissed = (
        out["is_wicket"].fillna(False)
        & (out["dismissed_player_id"] == out["striker_id"])
    )
    dismissed_a = striker_dismissed & (
        out["dismissal_type_clean"].fillna("") != "Retire Out"
    )
    dismissed = dismissed_a
    if scenario.dismissal_definition == "B":
        dismissed = dismissed & (extras != "wide")
    elif scenario.dismissal_definition != "A":
        raise ValueError(
            f"Unknown dismissal definition: {scenario.dismissal_definition}"
        )
    out["D"] = dismissed.astype(float)
    # Stage 4.2 Section 8.7 holds the personal baseline at primary
    # Definition A even in the Definition B sensitivity; only the pressure
    # numerator changes.  Keeping this column separate reproduces the
    # published Definition B reference moments and player table.
    out["D_baseline"] = dismissed_a.astype(float)

    out["bowler_runs"] = np.where(
        extras.isin(["wide", "overstep", "other"]),
        out["batter_runs"].astype(float) + out["extras_runs"].astype(float),
        out["batter_runs"].astype(float),
    )

    bowler_wicket = out["is_bowler_wicket"].fillna(False).astype(bool)
    if scenario.wide_stump_action == "remove":
        bowler_wicket = bowler_wicket & ~(
            (extras == "wide")
            & (out["dismissal_type_clean"].fillna("") == "Stump")
        )
    elif scenario.wide_stump_action != "retain":
        raise ValueError(
            f"Unknown wide stump action: {scenario.wide_stump_action}"
        )
    out["bowler_wicket_metric"] = bowler_wicket.astype(float)

    if scenario.season_weight == "equal":
        for col in ("w_bat", "w_bowl"):
            totals = out.groupby(["match_format", "season"])[col].transform("sum")
            out[col] = (out[col] / totals.replace(0.0, np.nan)).fillna(0.0)
    elif scenario.season_weight != "delivery":
        raise ValueError(f"Unknown season weight: {scenario.season_weight}")
    return out


# ---------------------------------------------------------------------------
# Format-level aggregation
# ---------------------------------------------------------------------------
def _name_map(df: pd.DataFrame, id_col: str, name_col: str) -> dict:
    names = (
        df[[id_col, name_col]]
        .dropna(subset=[id_col])
        .drop_duplicates(subset=[id_col])
        .set_index(id_col)[name_col]
    )
    return names.to_dict()


def _baseline_frame(df: pd.DataFrame, p_col: str, cutoff: float) -> pd.DataFrame:
    p = df[p_col]
    return df[p.notna() & (p < cutoff)].copy()


def build_batter_format_records_param(
    df: pd.DataFrame, scenario: Scenario, names: dict
) -> pd.DataFrame:
    """Build one batter-format record under a scenario."""
    pressure = df[df["p_bat"] >= scenario.pressure_cutoff].copy()
    if pressure.empty:
        return pd.DataFrame()

    pressure["w2"] = np.square(pressure["w_bat"])
    pressure["wr"] = pressure["w_bat"] * pressure["batter_runs"].astype(float)
    pressure["wbf"] = pressure["w_bat"] * pressure["BF"]
    pressure["wbf2"] = np.square(pressure["wbf"])
    pressure["wlegal"] = pressure["w_bat"] * pressure["legal"]
    pressure["wlegal2"] = np.square(pressure["wlegal"])
    pressure["wbound"] = pressure["w_bat"] * pressure["boundary_batter"]
    pressure["wdot"] = pressure["w_bat"] * pressure["dot_i"]
    pressure["wD"] = pressure["w_bat"] * pressure["D"]

    rec = (
        pressure.groupby(["match_format", "striker_id"], as_index=False)
        .agg(
            N_raw=("match_id", "size"),
            M_format=("match_id", "nunique"),
            sum_w=("w_bat", "sum"),
            sum_w2=("w2", "sum"),
            sum_wr=("wr", "sum"),
            sum_wbf=("wbf", "sum"),
            sum_wbf2=("wbf2", "sum"),
            sum_wlegal=("wlegal", "sum"),
            sum_wlegal2=("wlegal2", "sum"),
            sum_wbound=("wbound", "sum"),
            sum_wdot=("wdot", "sum"),
            sum_wD=("wD", "sum"),
        )
    )
    rec = rec.rename(columns={"striker_id": "player_id"})
    rec["role"] = "batter"
    rec["N_eff_del"] = np.square(rec["sum_w"]) / rec["sum_w2"]
    rec["N_eff_BF"] = np.square(rec["sum_wbf"]) / rec["sum_wbf2"].replace(0, np.nan)
    rec["N_eff_legal"] = (
        np.square(rec["sum_wlegal"]) / rec["sum_wlegal2"].replace(0, np.nan)
    )
    rec["SR_P"] = 100.0 * rec["sum_wr"] / rec["sum_wbf"].replace(0, np.nan)
    rec["Boundary_P"] = (
        100.0 * rec["sum_wbound"] / rec["sum_wbf"].replace(0, np.nan)
    )
    rec["Dot_P"] = 100.0 * rec["sum_wdot"] / rec["sum_wlegal"].replace(0, np.nan)
    rec["DR_P"] = 100.0 * rec["sum_wD"] / rec["sum_wbf"].replace(0, np.nan)

    baseline = _baseline_frame(df, "p_bat", scenario.pressure_cutoff)
    baseline["br"] = baseline["batter_runs"].astype(float)
    baseline["bBF"] = baseline["BF"]
    baseline["bD"] = baseline["D_baseline"]
    baseline["bdot"] = baseline["dot_i"]
    baseline["blegal"] = baseline["legal"]
    base = (
        baseline.groupby(["match_format", "striker_id"], as_index=False)
        .agg(
            baseline_BF=("bBF", "sum"),
            baseline_legal=("blegal", "sum"),
            base_runs=("br", "sum"),
            base_dot=("bdot", "sum"),
            base_D=("bD", "sum"),
            base_deliveries=("match_id", "size"),
            base_matches=("match_id", "nunique"),
        )
        .rename(columns={"striker_id": "player_id"})
    )
    base["SR_base"] = 100.0 * base["base_runs"] / base["baseline_BF"].replace(0, np.nan)
    base["Dot_base"] = (
        100.0 * base["base_dot"] / base["baseline_legal"].replace(0, np.nan)
    )
    base["DR_base"] = 100.0 * base["base_D"] / base["baseline_BF"].replace(0, np.nan)

    rec = rec.merge(
        base[
            [
                "match_format", "player_id", "baseline_BF", "baseline_legal",
                "base_deliveries", "base_matches", "SR_base", "Dot_base", "DR_base",
            ]
        ],
        on=["match_format", "player_id"],
        how="left",
    )
    rec["baseline_ok"] = (
        (rec["baseline_BF"].fillna(0) >= 120)
        & (rec["baseline_legal"].fillna(0) >= 120)
    )
    rec["dSR"] = rec["SR_P"] - rec["SR_base"]
    rec["dDot"] = rec["Dot_base"] - rec["Dot_P"]
    rec["dDR"] = rec["DR_base"] - rec["DR_P"]

    rec["den_dSR"] = rec["sum_wbf"]
    rec["den_SR_P"] = rec["sum_wbf"]
    rec["den_Boundary_P"] = rec["sum_wbf"]
    rec["den_dDot"] = rec["sum_wlegal"]
    rec["den_dDR"] = rec["sum_wbf"]
    rec["denoms_ok"] = (
        (rec["den_dSR"].fillna(0) > 0)
        & (rec["den_SR_P"].fillna(0) > 0)
        & (rec["den_Boundary_P"].fillna(0) > 0)
        & (rec["den_dDot"].fillna(0) > 0)
        & (rec["den_dDR"].fillna(0) > 0)
    )
    rec["format_gate"] = (
        (rec["N_raw"] >= scenario.raw_gate)
        & (rec["N_eff_del"] >= scenario.neff_gate)
    )
    if scenario.eligibility == "per_format_m10":
        rec["format_gate"] = rec["format_gate"] & (rec["M_format"] >= scenario.match_gate)
    rec = _add_shrunk_and_z_param(rec, "batter", scenario)
    rec["finite_Z"] = np.isfinite(rec["Z_comp_format"])
    rec["composite_ready"] = (
        rec["format_gate"]
        & rec["baseline_ok"]
        & rec["denoms_ok"]
        & rec["finite_Z"]
    )
    rec["player_name"] = rec["player_id"].map(names)
    rec["format_label"] = rec["match_format"].map(FORMAT_LABELS)
    return rec


def build_bowler_format_records_param(
    df: pd.DataFrame, scenario: Scenario, names: dict
) -> pd.DataFrame:
    """Build one bowler-format record under a scenario."""
    pressure = df[df["p_bowl"] >= scenario.pressure_cutoff].copy()
    if pressure.empty:
        return pd.DataFrame()

    pressure["w2"] = np.square(pressure["w_bowl"])
    pressure["wr"] = pressure["w_bowl"] * pressure["bowler_runs"].astype(float)
    pressure["wlegal"] = pressure["w_bowl"] * pressure["legal"]
    pressure["wlegal2"] = np.square(pressure["wlegal"])
    pressure["wwkt"] = pressure["w_bowl"] * pressure["bowler_wicket_metric"]
    pressure["wdot"] = pressure["w_bowl"] * pressure["dot_i"]
    pressure["wbound"] = pressure["w_bowl"] * pressure["boundary_bowler"]

    rec = (
        pressure.groupby(["match_format", "bowler_id"], as_index=False)
        .agg(
            N_raw=("match_id", "size"),
            M_format=("match_id", "nunique"),
            sum_w=("w_bowl", "sum"),
            sum_w2=("w2", "sum"),
            sum_wr=("wr", "sum"),
            sum_wlegal=("wlegal", "sum"),
            sum_wlegal2=("wlegal2", "sum"),
            sum_wwkt=("wwkt", "sum"),
            sum_wdot=("wdot", "sum"),
            sum_wbound=("wbound", "sum"),
        )
    )
    rec = rec.rename(columns={"bowler_id": "player_id"})
    rec["role"] = "bowler"
    rec["N_eff_del"] = np.square(rec["sum_w"]) / rec["sum_w2"]
    rec["N_eff_legal"] = (
        np.square(rec["sum_wlegal"]) / rec["sum_wlegal2"].replace(0, np.nan)
    )
    rec["Econ_P"] = 6.0 * rec["sum_wr"] / rec["sum_wlegal"].replace(0, np.nan)
    rec["WktRate_P"] = rec["sum_wwkt"] / rec["sum_wlegal"].replace(0, np.nan)
    rec["Dot_bowl_P"] = (
        100.0 * rec["sum_wdot"] / rec["sum_wlegal"].replace(0, np.nan)
    )
    rec["BoundaryConc_P"] = (
        100.0 * rec["sum_wbound"] / rec["sum_wlegal"].replace(0, np.nan)
    )

    baseline = _baseline_frame(df, "p_bowl", scenario.pressure_cutoff)
    baseline["br"] = baseline["bowler_runs"].astype(float)
    baseline["blegal"] = baseline["legal"]
    baseline["bdot"] = baseline["dot_i"]
    baseline["bbound"] = baseline["boundary_bowler"]
    base = (
        baseline.groupby(["match_format", "bowler_id"], as_index=False)
        .agg(
            baseline_legal=("blegal", "sum"),
            base_runs=("br", "sum"),
            base_dot=("bdot", "sum"),
            base_bound=("bbound", "sum"),
            base_deliveries=("match_id", "size"),
            base_matches=("match_id", "nunique"),
        )
        .rename(columns={"bowler_id": "player_id"})
    )
    base["Econ_base"] = (
        6.0 * base["base_runs"] / base["baseline_legal"].replace(0, np.nan)
    )
    base["Dot_base"] = (
        100.0 * base["base_dot"] / base["baseline_legal"].replace(0, np.nan)
    )
    base["BoundaryConc_base"] = (
        100.0 * base["base_bound"] / base["baseline_legal"].replace(0, np.nan)
    )

    rec = rec.merge(
        base[
            [
                "match_format", "player_id", "baseline_legal", "base_deliveries",
                "base_matches", "Econ_base", "Dot_base", "BoundaryConc_base",
            ]
        ],
        on=["match_format", "player_id"],
        how="left",
    )
    rec["baseline_ok"] = rec["baseline_legal"].fillna(0) >= 120
    rec["dEcon"] = rec["Econ_base"] - rec["Econ_P"]

    rec["den_dEcon"] = rec["sum_wlegal"]
    rec["den_Econ_P"] = rec["sum_wlegal"]
    rec["den_WktRate_P"] = rec["sum_wlegal"]
    rec["den_Dot_bowl_P"] = rec["sum_wlegal"]
    rec["den_BoundaryConc_P"] = rec["sum_wlegal"]
    rec["denoms_ok"] = (
        (rec["den_dEcon"].fillna(0) > 0)
        & (rec["den_Econ_P"].fillna(0) > 0)
        & (rec["den_WktRate_P"].fillna(0) > 0)
        & (rec["den_Dot_bowl_P"].fillna(0) > 0)
        & (rec["den_BoundaryConc_P"].fillna(0) > 0)
    )
    rec["format_gate"] = (
        (rec["N_raw"] >= scenario.raw_gate)
        & (rec["N_eff_del"] >= scenario.neff_gate)
    )
    if scenario.eligibility == "per_format_m10":
        rec["format_gate"] = rec["format_gate"] & (rec["M_format"] >= scenario.match_gate)
    rec = _add_shrunk_and_z_param(rec, "bowler", scenario)
    rec["finite_Z"] = np.isfinite(rec["Z_comp_format"])
    rec["composite_ready"] = (
        rec["format_gate"]
        & rec["baseline_ok"]
        & rec["denoms_ok"]
        & rec["finite_Z"]
    )
    rec["player_name"] = rec["player_id"].map(names)
    rec["format_label"] = rec["match_format"].map(FORMAT_LABELS)
    return rec


def _add_shrunk_and_z_param(
    rec: pd.DataFrame, role: str, scenario: Scenario
) -> pd.DataFrame:
    """Apply approved shrinkage and reference moments with a parameterized K."""
    metrics = BATTER_METRICS if role == "batter" else BOWLER_METRICS
    out = rec.copy()
    terms = []
    z_cols = []
    overrides = SENSITIVITY_REFERENCE_MOMENTS.get(scenario.scenario_id, {})

    for name, weight, raw_col, neff_col, use_peer, sign in metrics:
        effective_neff_col = neff_col
        if role == "bowler":
            if scenario.neff_scope == "all_deliveries":
                effective_neff_col = "N_eff_del"
            elif name == "WktRate_P" and scenario.wicket_neff == "all_deliveries":
                effective_neff_col = "N_eff_del"
        neff = out[effective_neff_col].astype(float)
        raw = out[raw_col].astype(float)
        prior = (
            out["match_format"].map(lambda f: MU_PEER[(f, name)])
            if use_peer
            else 0.0
        )
        weight_neff = neff / (neff + scenario.shrinkage_k)
        shrunk = (
            weight_neff * raw
            + (scenario.shrinkage_k / (neff + scenario.shrinkage_k)) * prior
        )
        out[f"shrunk_{name}"] = shrunk

        moment_by_format = {}
        for fmt in out["match_format"].unique():
            moment_by_format[fmt] = overrides.get(
                (role, fmt, name), REFERENCE_MOMENTS[(role, fmt, name)]
            )
        mean = out["match_format"].map(lambda f: moment_by_format[f][0])
        sd = out["match_format"].map(lambda f: moment_by_format[f][1])
        out[f"z_{name}"] = (shrunk - mean) / sd

        term = sign * weight * out[f"z_{name}"]
        out[f"term_{name}"] = term
        terms.append(term)
        z_cols.append(f"z_{name}")

    out["Z_comp_format"] = sum(terms)
    out["_z_all_finite"] = out[z_cols].apply(
        lambda row: bool(np.isfinite(row).all()), axis=1
    )
    out["finite_Z"] = out["_z_all_finite"] & np.isfinite(out["Z_comp_format"])
    out = out.drop(columns=["_z_all_finite"])
    return out


# ---------------------------------------------------------------------------
# Eligibility and player scoring
# ---------------------------------------------------------------------------
def add_player_eligibility_param(
    rec: pd.DataFrame, role: str, scenario: Scenario
) -> pd.DataFrame:
    """Attach F, M_role, M_all and the scenario's final eligibility gate."""
    out = rec.copy()
    id_col = "player_id"

    f_records = out[out["composite_ready"]].copy()
    m_role = (
        f_records.groupby(id_col)["M_format"].sum().rename("M_role")
        if not f_records.empty
        else pd.Series(dtype=float, name="M_role")
    )
    m_all = out.groupby(id_col)["M_format"].sum().rename("M_all")

    out["M_role"] = out[id_col].map(m_role).fillna(0).astype(int)
    out["M_all"] = out[id_col].map(m_all).fillna(0).astype(int)
    out["F_nonempty"] = out[id_col].isin(m_role.index)
    if scenario.eligibility == "m_all":
        out["ranking_eligible"] = out["composite_ready"] & (
            out["M_all"] >= scenario.match_gate
        )
    else:
        out["ranking_eligible"] = out["composite_ready"] & (
            out["M_role"] >= scenario.match_gate
        )

    def record_status(row):
        if row["ranking_eligible"]:
            return STATUS_RANKING
        if row["composite_ready"]:
            return STATUS_M_BREADTH
        if not bool(row["baseline_ok"]):
            return STATUS_BASELINE
        return STATUS_SAMPLE

    out["record_status"] = out.apply(record_status, axis=1)
    out["exclusion_detail"] = out.apply(
        lambda row: _record_exclusion_detail(row, scenario), axis=1
    )
    out["role"] = role
    return out


def _record_exclusion_detail(row, scenario: Scenario) -> str:
    reasons = []
    if row["N_raw"] < scenario.raw_gate:
        reasons.append(f"N_raw<{scenario.raw_gate}")
    if not np.isfinite(row["N_eff_del"]) or row["N_eff_del"] < scenario.neff_gate:
        reasons.append(f"N_eff_del<{scenario.neff_gate:g}")
    if scenario.eligibility == "per_format_m10" and row["M_format"] < scenario.match_gate:
        reasons.append(f"M_format<{scenario.match_gate}")
    if not bool(row["baseline_ok"]):
        reasons.append("baseline_insufficient")
    if not bool(row["denoms_ok"]):
        reasons.append("zero_metric_denominator")
    if not bool(row["finite_Z"]):
        reasons.append("nonfinite_composite")
    if row["composite_ready"] and scenario.eligibility == "m_all":
        if row["M_all"] < scenario.match_gate:
            reasons.append(f"M_all<{scenario.match_gate}")
    elif row["composite_ready"] and row["M_role"] < scenario.match_gate:
        reasons.append(f"M_role<{scenario.match_gate}")
    return "; ".join(reasons)


def build_player_scoring_param(
    records: pd.DataFrame, role: str, scenario: Scenario
) -> pd.DataFrame:
    """Build one row per player per role under a scenario."""
    id_col = "player_id"
    rows = []
    for player_id, group in records.groupby(id_col, sort=False):
        f_group = group[group["composite_ready"]].copy()
        row = {
            "role": role,
            "player_id": int(player_id),
            "player_name": group["player_name"].dropna().iloc[0]
            if group["player_name"].notna().any()
            else None,
            "F_formats": "",
            "n_formats_F": 0,
            "F_nonempty": not f_group.empty,
            "M_role": int(group["M_role"].iloc[0]),
            "M_all": int(group["M_all"].iloc[0]),
            "sum_N_raw_F": 0,
            "sum_N_eff_del_F": 0.0,
            "Z_comp": np.nan,
            "Z_std": np.nan,
            "Reliability": np.nan,
            "ranking_eligible": False,
            "status": STATUS_SAMPLE,
            "exclusion_detail": "",
            "calibration_population": not f_group.empty,
        }

        if not f_group.empty:
            f_sorted = f_group.copy()
            f_sorted["_fmt_order"] = f_sorted["match_format"].map(
                {fmt: i for i, fmt in enumerate(FORMAT_ORDER)}
            )
            f_sorted = f_sorted.sort_values("_fmt_order")
            row["F_formats"] = ",".join(f_sorted["format_label"].tolist())
            row["n_formats_F"] = len(f_sorted)
            row["sum_N_raw_F"] = int(f_sorted["N_raw"].sum())
            row["sum_N_eff_del_F"] = float(f_sorted["N_eff_del"].sum())
            if scenario.cross_format_weight == "equal":
                row["Z_comp"] = float(f_sorted["Z_comp_format"].mean())
            elif scenario.cross_format_weight == "neff":
                w = f_sorted["N_eff_del"].astype(float)
                row["Z_comp"] = float(
                    (f_sorted["Z_comp_format"].astype(float) * w).sum() / w.sum()
                )
            else:
                raise ValueError(
                    "Capped N_eff weighting requires a registered numeric C and "
                    "is not implemented."
                )

            cal = CALIBRATION[role]
            row["Z_std"] = (row["Z_comp"] - cal["mu"]) / cal["sigma"]
            row["Reliability"] = 100.0 / (
                1.0 + np.exp(-RELIABILITY_GAMMA * row["Z_std"])
            )
            if scenario.eligibility == "m_all":
                row["ranking_eligible"] = row["M_all"] >= scenario.match_gate
            else:
                row["ranking_eligible"] = row["M_role"] >= scenario.match_gate
            if row["ranking_eligible"]:
                row["status"] = STATUS_RANKING
            else:
                row["status"] = STATUS_M_BREADTH
                if scenario.eligibility == "m_all":
                    row["exclusion_detail"] = f"M_all<{scenario.match_gate}"
                else:
                    row["exclusion_detail"] = f"M_role<{scenario.match_gate}"
        else:
            if (~group["baseline_ok"].astype(bool)).any():
                row["status"] = STATUS_BASELINE
                row["exclusion_detail"] = "baseline_insufficient"
            else:
                row["status"] = STATUS_SAMPLE
                row["exclusion_detail"] = "format gate / denominator / composite failed"

        rows.append(row)

    players = pd.DataFrame(rows)
    if players.empty:
        return players
    return assign_ranks_param(players)


def assign_ranks_param(players: pd.DataFrame) -> pd.DataFrame:
    """Apply the approved deterministic ranking and tie-break order."""
    out = players.copy()
    out["final_rank"] = pd.Series(pd.NA, index=out.index, dtype="Int64")

    eligible = out[out["ranking_eligible"]].copy()
    eligible = eligible.sort_values(
        by=[
            "Z_comp",
            "sum_N_eff_del_F",
            "M_role",
            "sum_N_raw_F",
            "player_id",
        ],
        ascending=[False, False, False, False, True],
        kind="mergesort",
    )
    eligible["final_rank"] = np.arange(1, len(eligible) + 1)
    out.loc[eligible.index, "final_rank"] = eligible["final_rank"].astype("Int64")

    out["_rank_sort"] = out["final_rank"].fillna(10**9).astype(int)
    out = out.sort_values(
        ["_rank_sort", "player_id"], ascending=[True, True], kind="mergesort"
    ).drop(columns=["_rank_sort"])
    return out.reset_index(drop=True)


def top_n(players: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (
        players[players["ranking_eligible"]]
        .sort_values("final_rank", kind="mergesort")
        .head(n)
        .copy()
    )


# ---------------------------------------------------------------------------
# Scenario orchestration
# ---------------------------------------------------------------------------
def run_scenario(
    base: pd.DataFrame,
    scenario: Scenario,
    keep_deliveries: bool = False,
) -> dict:
    """Run one registered scenario and return tables plus diagnostics."""
    if scenario.status in {"BLOCKED_NOT_APPROVED", "OPTIONAL_NOT_RUN"}:
        raise ValueError(f"Scenario {scenario.scenario_id} is not executable.")

    df = _scenario_corpus(base, scenario)
    fallback = scenario.include_48610_chase
    deliveries = compute_pressure_features_param(df, scenario, unresolved_fallback=fallback)
    deliveries = add_delivery_metrics_param(deliveries, scenario)

    batter_names = _name_map(deliveries, "striker_id", "striker_name")
    bowler_names = _name_map(deliveries, "bowler_id", "bowler_name")

    batter_records = build_batter_format_records_param(
        deliveries, scenario, batter_names
    )
    bowler_records = build_bowler_format_records_param(
        deliveries, scenario, bowler_names
    )
    batter_records = add_player_eligibility_param(
        batter_records, "batter", scenario
    )
    bowler_records = add_player_eligibility_param(
        bowler_records, "bowler", scenario
    )
    batter_players = build_player_scoring_param(batter_records, "batter", scenario)
    bowler_players = build_player_scoring_param(bowler_records, "bowler", scenario)

    pressure_bat = deliveries[deliveries["p_bat"] >= scenario.pressure_cutoff]
    pressure_bowl = deliveries[deliveries["p_bowl"] >= scenario.pressure_cutoff]
    boundary_rows = pressure_bowl[pressure_bowl["boundary_bowler"] > 0]
    diagnostics = {
        "scenario_id": scenario.scenario_id,
        "corpus_rows": int(len(deliveries)),
        "matches": int(deliveries["match_id"].nunique()),
        "seasons": ",".join(
            sorted(deliveries["season"].dropna().astype(str).unique().tolist())
        ),
        "pressure_batter_rows": int(len(pressure_bat)),
        "pressure_bowler_rows": int(len(pressure_bowl)),
        "other_rows": int((deliveries["extras_type_clean"] == "other").sum()),
        "other_pressure_bowler_rows": int(
            (pressure_bowl["extras_type_clean"] == "other").sum()
        ),
        "other_legal_rows": int(
            ((deliveries["extras_type_clean"] == "other") & (deliveries["legal"] > 0)).sum()
        ),
        "widestump_pressure_rows": int(
            (
                (pressure_bowl["extras_type_clean"] == "wide")
                & (pressure_bowl["dismissal_type_clean"].fillna("") == "Stump")
            ).sum()
        ),
        "wide_dismissal_pressure_rows": int(
            (
                (pressure_bat["extras_type_clean"] == "wide")
                & (pressure_bat["D"] > 0)
            ).sum()
        ),
        "boundary_count_all": int(len(boundary_rows)),
        "boundary_count_legal_overstep": int(
            (
                boundary_rows["legal"].fillna(0).astype(bool)
                | (boundary_rows["extras_type_clean"] == "overstep")
            ).sum()
        ),
        "boundary_count_legal_only": int(
            boundary_rows["legal"].fillna(0).astype(bool).sum()
        ),
        "p_bat_mean": float(pressure_bat["p_bat"].mean()),
        "p_bowl_mean": float(pressure_bowl["p_bowl"].mean()),
    }

    result = {
        "scenario": scenario,
        "batter_records": batter_records,
        "bowler_records": bowler_records,
        "batter_players": batter_players,
        "bowler_players": bowler_players,
        "diagnostics": diagnostics,
    }
    if keep_deliveries:
        result["deliveries"] = deliveries
    return result


# ---------------------------------------------------------------------------
# Comparison and stability calculations
# ---------------------------------------------------------------------------
def top10_ids(players: pd.DataFrame) -> list[int]:
    top = top_n(players, 10)
    return [int(x) for x in top["player_id"].tolist()]


def _common_ranks(
    primary: pd.DataFrame, scenario: pd.DataFrame
) -> pd.DataFrame:
    p = primary[primary["ranking_eligible"]][["player_id", "final_rank", "Z_comp"]].rename(
        columns={"final_rank": "primary_rank", "Z_comp": "primary_Z"}
    )
    s = scenario[scenario["ranking_eligible"]][["player_id", "final_rank", "Z_comp"]].rename(
        columns={"final_rank": "scenario_rank", "Z_comp": "scenario_Z"}
    )
    return p.merge(s, on="player_id", how="inner", validate="one_to_one")


def correlate_common(
    primary: pd.DataFrame, scenario: pd.DataFrame
) -> dict:
    """Rank and score correlations on the common eligible population."""
    from scipy.stats import kendalltau, spearmanr

    common = _common_ranks(primary, scenario)
    n = len(common)
    out = {
        "common_n": int(n),
        "spearman_rank": np.nan,
        "kendall_rank": np.nan,
        "spearman_z": np.nan,
        "kendall_z": np.nan,
    }
    if n >= 3:
        out["spearman_rank"] = float(
            spearmanr(common["primary_rank"], common["scenario_rank"]).statistic
        )
        out["kendall_rank"] = float(
            kendalltau(common["primary_rank"], common["scenario_rank"]).statistic
        )
        out["spearman_z"] = float(
            spearmanr(common["primary_Z"], common["scenario_Z"]).statistic
        )
        out["kendall_z"] = float(
            kendalltau(common["primary_Z"], common["scenario_Z"]).statistic
        )
    if n:
        delta = (common["scenario_rank"] - common["primary_rank"]).astype(float)
        zdelta = (common["scenario_Z"] - common["primary_Z"]).astype(float)
        out["mean_abs_rank_change"] = float(delta.abs().mean())
        out["max_abs_rank_change"] = float(delta.abs().max())
        out["mean_rank_change"] = float(delta.mean())
        out["mean_z_change"] = float(zdelta.mean())
        out["max_abs_z_change"] = float(zdelta.abs().max())
    else:
        out.update(
            {
                "mean_abs_rank_change": np.nan,
                "max_abs_rank_change": np.nan,
                "mean_rank_change": np.nan,
                "mean_z_change": np.nan,
                "max_abs_z_change": np.nan,
            }
        )
    return out


def compare_top10(primary: pd.DataFrame, scenario: pd.DataFrame) -> dict:
    p_ids = top10_ids(primary)
    s_ids = top10_ids(scenario)
    p_set, s_set = set(p_ids), set(s_ids)
    retained = [player_id for player_id in p_ids if player_id in s_set]
    entrants = [player_id for player_id in s_ids if player_id not in p_set]
    leavers = [player_id for player_id in p_ids if player_id not in s_set]
    union = p_set | s_set
    return {
        "primary_top10": p_ids,
        "scenario_top10": s_ids,
        "top10_overlap": len(retained),
        "top10_jaccard": (len(retained) / len(union)) if union else np.nan,
        "retained": retained,
        "entrants": entrants,
        "leavers": leavers,
    }


def align_scenario_players(
    primary_players: pd.DataFrame,
    scenario_players: pd.DataFrame,
    scenario_id: str,
    role: str,
) -> pd.DataFrame:
    """Union of primary and scenario player universes for one role."""
    keep = [
        "player_id", "player_name", "ranking_eligible", "final_rank", "Z_comp",
        "Z_std", "Reliability", "M_role", "M_all", "sum_N_raw_F",
        "sum_N_eff_del_F", "F_formats", "status",
    ]
    p = primary_players[keep].rename(
        columns={
            "player_name": "primary_player_name",
            "ranking_eligible": "primary_eligible",
            "final_rank": "primary_rank",
            "Z_comp": "primary_Z_comp",
            "Z_std": "primary_Z_std",
            "Reliability": "primary_Reliability",
            "M_role": "primary_M_role",
            "M_all": "primary_M_all",
            "sum_N_raw_F": "primary_sum_N_raw_F",
            "sum_N_eff_del_F": "primary_sum_N_eff_del_F",
            "F_formats": "primary_F_formats",
            "status": "primary_status",
        }
    )
    s = scenario_players[keep].rename(
        columns={
            "player_name": "scenario_player_name",
            "ranking_eligible": "scenario_eligible",
            "final_rank": "scenario_rank",
            "Z_comp": "scenario_Z_comp",
            "Z_std": "scenario_Z_std",
            "Reliability": "scenario_Reliability",
            "M_role": "scenario_M_role",
            "M_all": "scenario_M_all",
            "sum_N_raw_F": "scenario_sum_N_raw_F",
            "sum_N_eff_del_F": "scenario_sum_N_eff_del_F",
            "F_formats": "scenario_F_formats",
            "status": "scenario_status",
        }
    )
    out = p.merge(s, on="player_id", how="outer")
    out["player_name"] = out["scenario_player_name"].where(
        out["scenario_player_name"].notna(), out["primary_player_name"]
    )
    out["scenario_id"] = scenario_id
    out["role"] = role
    for col in ("primary_eligible", "scenario_eligible"):
        out[col] = out[col].fillna(False).astype(bool)
    out["in_primary_top10"] = out["primary_rank"].le(10) & out["primary_eligible"]
    out["in_scenario_top10"] = out["scenario_rank"].le(10) & out["scenario_eligible"]
    out["rank_change_vs_primary"] = (
        out["scenario_rank"].astype(float) - out["primary_rank"].astype(float)
    )
    out["Z_change_vs_primary"] = (
        out["scenario_Z_comp"].astype(float) - out["primary_Z_comp"].astype(float)
    )
    out["Reliability_change_vs_primary"] = (
        out["scenario_Reliability"].astype(float)
        - out["primary_Reliability"].astype(float)
    )
    return out
