"""
Stage 5 primary scoring engine.

Implements the approved Stage 4.2 methodology without changing formulas,
weights or thresholds.  The engine is deliberately split into small functions
so the pressure, aggregation, eligibility, calibration and ranking layers can
be tested independently.

No raw or approved pressure-feature dataset is written by this module.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from stage5_config import (
    AUDIT_CORPUS_ROWS,
    BATTER_METRICS,
    BINARY_LEVERAGE,
    BOWLER_METRICS,
    CALIBRATION,
    CRR_BASE,
    FORMAT_LABELS,
    FORMAT_ORDER,
    GAUSSIAN_WIDTH,
    MATCH_48610_ID,
    MATCH_GATE,
    MU_PEER,
    NEFF_GATE,
    PRESSURE_CUTOFF,
    RAW_GATE,
    REFERENCE_MOMENTS,
    RELIABILITY_GAMMA,
    SCORING_CORPUS_ROWS,
    SCORING_DATA_PATH,
    SHRINKAGE_K,
    WICKET_BASELINE,
)

READ_COLUMNS = [
    "match_id", "innings", "match_format", "match_status_category", "is_super_over",
    "striker_id", "striker_name", "bowler_id", "bowler_name",
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
# Loading and delivery-level features
# ---------------------------------------------------------------------------
def load_delivery_corpus(path=SCORING_DATA_PATH) -> pd.DataFrame:
    """Load the completed, non-Super-Over audit corpus.

    Returns 192,056 rows before the Q9 Match 48610 exclusion.  The caller
    applies the scoring exclusion explicitly.
    """
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


def scoring_corpus(df: pd.DataFrame) -> pd.DataFrame:
    """Apply Q9: exclude the 93 Match 48610 second-innings deliveries."""
    out = df[
        ~((df["match_id"] == MATCH_48610_ID) & (df["innings"] == 2))
    ].copy()
    if len(out) != SCORING_CORPUS_ROWS:
        raise ValueError(
            f"Expected {SCORING_CORPUS_ROWS:,} scoring rows, found {len(out):,}."
        )
    return out


def _sigmoid(z):
    return 100.0 / (1.0 + np.exp(-z))


def compute_pressure_features(
    df: pd.DataFrame, unresolved_fallback: bool = False
) -> pd.DataFrame:
    """Compute P_bat, P_bowl and delivery weights.

    First innings use the approved P1 equations.  Resolved chases use P2.
    Second-innings rows without a resolved target are marked EXCLUDED in the
    primary path.  ``unresolved_fallback=True`` is used only to reproduce the
    documented audit-corpus boundary counts, where the Match 48610 chase is
    evaluated under the explicitly labelled P1 fallback sensitivity.  The
    scoring corpus removes those rows before any scoring calculation.
    """
    out = df.copy()
    b = out["legal_balls_before"].astype(float).to_numpy()
    mb = out["max_balls"].astype(float).to_numpy()
    balls_rem = mb - b
    runs_before = out["runs_before"].astype(float).to_numpy()
    wickets_before = out["wickets_before"].astype(float).to_numpy()
    runs_req = out["runs_required"].astype(float).to_numpy()
    is_t20 = (out["match_format"] == "T20").to_numpy()

    crr = np.where(is_t20, CRR_BASE["T20"], CRR_BASE["T20I"])
    wicket_base = np.where(
        is_t20, WICKET_BASELINE["T20"], WICKET_BASELINE["T20I"]
    )

    # First innings (P1)
    expected_runs = crr * b / 6.0
    expected_wickets = (
        wicket_base * (mb / 120.0) * np.power(b / mb, 0.85)
    )
    s_runs = np.tanh((expected_runs - runs_before) / 15.0)
    s_wickets = np.clip(
        wickets_before / (expected_wickets + 0.50), 0.0, 3.0
    ) / 3.0
    w_stab = b / (b + 12.0)
    u_phase = np.power(b / mb, 1.50)

    z_bat1 = (
        2.20 * s_wickets
        + 1.80 * (w_stab * s_runs)
        + 1.50 * u_phase
        - 1.50
    )
    z_bowl1 = (
        2.00 * (-s_runs)
        + 1.50 * (1.0 - s_wickets)
        + 1.80 * u_phase
        - 1.80
    )
    p_bat1 = _sigmoid(z_bat1)
    p_bowl1 = _sigmoid(z_bowl1)

    # Second innings (P2)
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
    z_bat2 = (
        2.50 * np.log(np.maximum(0.10, demand))
        + 1.80 * time_decay
        - 1.20
    )

    h = np.sqrt(w_rem / 10.0)
    expected_runs_bowl = crr * (balls_rem / 6.0) * h
    surplus = expected_runs_bowl - runs_req
    c_match = np.exp(-(surplus ** 2) / (2.0 * GAUSSIAN_WIDTH ** 2))
    core = 5.50 * (0.65 + 0.35 * h) + 1.20 * time_decay
    leverage = np.where(
        (balls_rem <= 12) & (runs_req > 0) & (runs_req <= 12) & (w_rem == 1),
        BINARY_LEVERAGE,
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
        np.isfinite(p_bat) & (p_bat >= PRESSURE_CUTOFF),
        np.square(p_bat / 100.0),
        0.0,
    )
    out["w_bowl"] = np.where(
        np.isfinite(p_bowl) & (p_bowl >= PRESSURE_CUTOFF),
        np.square(p_bowl / 100.0),
        0.0,
    )
    return out


def add_delivery_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add approved delivery attribution fields.

    `other` remains provisional no-ball-like: it counts as a ball faced, is
    non-legal, counts a batter boundary, and charges the bowler batter runs
    plus extras.
    """
    out = df.copy()
    extras = out["extras_type_clean"].fillna("none")

    out["BF"] = (extras != "wide").astype(float)
    out["legal"] = out["is_legal_delivery"].fillna(False).astype(float)
    out["dot_i"] = out["is_dot_ball"].fillna(False).astype(float)
    out["boundary"] = (
        out["is_four"].fillna(False) | out["is_six"].fillna(False)
    ).astype(float)

    striker_dismissed = (
        out["is_wicket"].fillna(False)
        & (out["dismissed_player_id"] == out["striker_id"])
    )
    out["D"] = (
        striker_dismissed
        & (out["dismissal_type_clean"].fillna("") != "Retire Out")
    ).astype(float)

    out["bowler_runs"] = np.where(
        extras.isin(["wide", "overstep", "other"]),
        out["batter_runs"].astype(float) + out["extras_runs"].astype(float),
        out["batter_runs"].astype(float),
    )
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


def build_batter_format_records(df: pd.DataFrame) -> pd.DataFrame:
    """Build one batter-format record per player and format."""
    pressure = df[df["p_bat"] >= PRESSURE_CUTOFF].copy()
    if pressure.empty:
        return pd.DataFrame()

    pressure["w2"] = np.square(pressure["w_bat"])
    pressure["wr"] = pressure["w_bat"] * pressure["batter_runs"].astype(float)
    pressure["wbf"] = pressure["w_bat"] * pressure["BF"]
    pressure["wbf2"] = np.square(pressure["wbf"])
    pressure["wlegal"] = pressure["w_bat"] * pressure["legal"]
    pressure["wlegal2"] = np.square(pressure["wlegal"])
    pressure["wbound"] = pressure["w_bat"] * pressure["boundary"]
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
    rec["Dot_P"] = (
        100.0 * rec["sum_wdot"] / rec["sum_wlegal"].replace(0, np.nan)
    )
    rec["DR_P"] = 100.0 * rec["sum_wD"] / rec["sum_wbf"].replace(0, np.nan)

    baseline = df[df["p_bat"] < PRESSURE_CUTOFF].copy()
    baseline["br"] = baseline["batter_runs"].astype(float)
    baseline["bBF"] = baseline["BF"]
    baseline["bD"] = baseline["D"]
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
        (rec["N_raw"] >= RAW_GATE) & (rec["N_eff_del"] >= NEFF_GATE)
    )
    rec = _add_shrunk_and_z(rec, "batter")
    rec["finite_Z"] = np.isfinite(rec["Z_comp_format"])
    rec["composite_ready"] = (
        rec["format_gate"]
        & rec["baseline_ok"]
        & rec["denoms_ok"]
        & rec["finite_Z"]
    )

    names = _name_map(df, "striker_id", "striker_name")
    rec["player_name"] = rec["player_id"].map(names)
    rec["format_label"] = rec["match_format"].map(FORMAT_LABELS)
    return rec


def build_bowler_format_records(df: pd.DataFrame) -> pd.DataFrame:
    """Build one bowler-format record per player and format."""
    pressure = df[df["p_bowl"] >= PRESSURE_CUTOFF].copy()
    if pressure.empty:
        return pd.DataFrame()

    pressure["w2"] = np.square(pressure["w_bowl"])
    pressure["wr"] = pressure["w_bowl"] * pressure["bowler_runs"].astype(float)
    pressure["wlegal"] = pressure["w_bowl"] * pressure["legal"]
    pressure["wlegal2"] = np.square(pressure["wlegal"])
    pressure["wwkt"] = pressure["w_bowl"] * pressure["is_bowler_wicket"].fillna(False).astype(float)
    pressure["wdot"] = pressure["w_bowl"] * pressure["dot_i"]
    pressure["wbound"] = pressure["w_bowl"] * pressure["boundary"]

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

    baseline = df[df["p_bowl"] < PRESSURE_CUTOFF].copy()
    baseline["br"] = baseline["bowler_runs"].astype(float)
    baseline["blegal"] = baseline["legal"]
    baseline["bdot"] = baseline["dot_i"]
    baseline["bbound"] = baseline["boundary"]
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
        (rec["N_raw"] >= RAW_GATE) & (rec["N_eff_del"] >= NEFF_GATE)
    )
    rec = _add_shrunk_and_z(rec, "bowler")
    rec["finite_Z"] = np.isfinite(rec["Z_comp_format"])
    rec["composite_ready"] = (
        rec["format_gate"]
        & rec["baseline_ok"]
        & rec["denoms_ok"]
        & rec["finite_Z"]
    )

    names = _name_map(df, "bowler_id", "bowler_name")
    rec["player_name"] = rec["player_id"].map(names)
    rec["format_label"] = rec["match_format"].map(FORMAT_LABELS)
    return rec


def _add_shrunk_and_z(rec: pd.DataFrame, role: str) -> pd.DataFrame:
    """Apply approved shrinkage, reference moments and composite weights."""
    metrics = BATTER_METRICS if role == "batter" else BOWLER_METRICS
    out = rec.copy()
    terms = []
    z_cols = []

    for name, weight, raw_col, neff_col, use_peer, sign in metrics:
        neff = out[neff_col].astype(float)
        raw = out[raw_col].astype(float)
        prior = (
            out["match_format"].map(lambda f: MU_PEER[(f, name)])
            if use_peer
            else 0.0
        )
        weight_neff = neff / (neff + SHRINKAGE_K)
        shrunk = weight_neff * raw + (SHRINKAGE_K / (neff + SHRINKAGE_K)) * prior
        out[f"shrunk_{name}"] = shrunk

        mean_sd = out["match_format"].map(
            lambda f: REFERENCE_MOMENTS[(role, f, name)]
        )
        mean = mean_sd.map(lambda x: x[0])
        sd = mean_sd.map(lambda x: x[1])
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
# Player eligibility, calibration and rankings
# ---------------------------------------------------------------------------
def add_player_eligibility(rec: pd.DataFrame, role: str) -> pd.DataFrame:
    """Attach F, M_role, M_all and the approved final eligibility gate."""
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
    out["ranking_eligible"] = out["composite_ready"] & (
        out["M_role"] >= MATCH_GATE
    )

    def record_status(row):
        if row["composite_ready"] and row["M_role"] >= MATCH_GATE:
            return STATUS_RANKING
        if row["composite_ready"]:
            return STATUS_M_BREADTH
        if not bool(row["baseline_ok"]):
            return STATUS_BASELINE
        return STATUS_SAMPLE

    out["record_status"] = out.apply(record_status, axis=1)
    out["exclusion_detail"] = out.apply(_record_exclusion_detail, axis=1)
    out["role"] = role
    return out


def _record_exclusion_detail(row) -> str:
    reasons = []
    if row["N_raw"] < RAW_GATE:
        reasons.append(f"N_raw<{RAW_GATE}")
    if not np.isfinite(row["N_eff_del"]) or row["N_eff_del"] < NEFF_GATE:
        reasons.append(f"N_eff_del<{NEFF_GATE:g}")
    if not bool(row["baseline_ok"]):
        reasons.append("baseline_insufficient")
    if not bool(row["denoms_ok"]):
        reasons.append("zero_metric_denominator")
    if not bool(row["finite_Z"]):
        reasons.append("nonfinite_composite")
    if row["composite_ready"] and row["M_role"] < MATCH_GATE:
        reasons.append(f"M_role<{MATCH_GATE}")
    return "; ".join(reasons)


def build_player_scoring(records: pd.DataFrame, role: str) -> pd.DataFrame:
    """Build one row per player per role with equal-weight format composite."""
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
            row["Z_comp"] = float(f_sorted["Z_comp_format"].mean())

            cal = CALIBRATION[role]
            row["Z_std"] = (row["Z_comp"] - cal["mu"]) / cal["sigma"]
            row["Reliability"] = 100.0 / (
                1.0 + np.exp(-RELIABILITY_GAMMA * row["Z_std"])
            )
            row["ranking_eligible"] = row["M_role"] >= MATCH_GATE
            if row["ranking_eligible"]:
                row["status"] = STATUS_RANKING
            else:
                row["status"] = STATUS_M_BREADTH
                row["exclusion_detail"] = f"M_role<{MATCH_GATE}"
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
    players = assign_ranks(players)
    return players


def assign_ranks(players: pd.DataFrame) -> pd.DataFrame:
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

    # Display order: ranked players first, then the remaining audit rows.
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
# Orchestration
# ---------------------------------------------------------------------------
def build_stage5_tables(df: pd.DataFrame | None = None) -> dict:
    """Build all Stage 5 scoring tables without writing files."""
    audit = load_delivery_corpus() if df is None else df.copy()
    # The audit table intentionally carries the labelled P1 fallback for the
    # unresolved Match 48610 chase so the documented audit counts reconcile.
    # The scoring corpus below removes those 93 rows before any scoring.
    audit = add_delivery_metrics(
        compute_pressure_features(audit, unresolved_fallback=True)
    )
    scoring = scoring_corpus(audit).copy()

    batter_records = add_player_eligibility(
        build_batter_format_records(scoring), "batter"
    )
    bowler_records = add_player_eligibility(
        build_bowler_format_records(scoring), "bowler"
    )
    batter_players = build_player_scoring(batter_records, "batter")
    bowler_players = build_player_scoring(bowler_records, "bowler")

    return {
        "audit": audit,
        "scoring": scoring,
        "batter_records": batter_records,
        "bowler_records": bowler_records,
        "batter_players": batter_players,
        "bowler_players": bowler_players,
        "top10_batters": top_n(batter_players, 10),
        "top10_bowlers": top_n(bowler_players, 10),
    }
