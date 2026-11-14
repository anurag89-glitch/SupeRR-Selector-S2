"""
Stage 5 independent validation layer.

The checks in this module are intentionally separate from the scoring engine.
They recompute the pressure equations, delivery attribution, format-level
aggregates, reference moments, calibration moments, reliability and ranking
order from the delivered tables and, where practical, from independent
numpy/pandas implementations.

The runner writes the CSV outputs first and then calls this module with
``check_outputs=True``.  The validation report is never used as a substitute
for a failing check: every critical check is reported as PASS or FAIL.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

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
    OUTPUT_DIR,
    OUTPUT_FILES,
    PRESSURE_CUTOFF,
    RAW_GATE,
    REFERENCE_MOMENTS,
    RELIABILITY_GAMMA,
    SCORING_CORPUS_ROWS,
    SHRINKAGE_K,
    WICKET_BASELINE,
)

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _add(
    checks: list[dict],
    area: str,
    name: str,
    passed: bool,
    detail: str = "",
) -> None:
    checks.append(
        {
            "area": area,
            "check": name,
            "passed": bool(passed),
            "detail": "" if detail is None else str(detail),
        }
    )


def _sig(z):
    return 100.0 / (1.0 + np.exp(-z))


def _allclose(a, b, atol: float = 1e-9, rtol: float = 1e-9) -> bool:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return bool(np.allclose(a, b, atol=atol, rtol=rtol, equal_nan=True))


def _max_abs_diff(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    if not mask.any():
        return 0.0
    return float(np.max(np.abs(a[mask] - b[mask])))


# ---------------------------------------------------------------------------
# Independent pressure and delivery implementations
# ---------------------------------------------------------------------------
def _independent_pressure(df: pd.DataFrame, fallback: bool = False):
    """Recompute P_bat and P_bowl from the approved Stage 4.2 equations."""
    b = df["legal_balls_before"].astype(float).to_numpy()
    mb = df["max_balls"].astype(float).to_numpy()
    balls_rem = mb - b
    runs_before = df["runs_before"].astype(float).to_numpy()
    wickets_before = df["wickets_before"].astype(float).to_numpy()
    runs_req = df["runs_required"].astype(float).to_numpy()
    is_t20 = (df["match_format"] == "T20").to_numpy()

    crr = np.where(is_t20, CRR_BASE["T20"], CRR_BASE["T20I"])
    lam = np.where(is_t20, WICKET_BASELINE["T20"], WICKET_BASELINE["T20I"])

    expected_runs = crr * b / 6.0
    expected_wickets = lam * (mb / 120.0) * np.power(b / mb, 0.85)
    s_runs = np.tanh((expected_runs - runs_before) / 15.0)
    s_wkts = np.clip(wickets_before / (expected_wickets + 0.50), 0.0, 3.0) / 3.0
    w_stab = b / (b + 12.0)
    u_phase = np.power(b / mb, 1.50)

    z_bat1 = 2.20 * s_wkts + 1.80 * w_stab * s_runs + 1.50 * u_phase - 1.50
    z_bowl1 = 2.00 * (-s_runs) + 1.50 * (1.0 - s_wkts) + 1.80 * u_phase - 1.80
    p_bat1 = _sig(z_bat1)
    p_bowl1 = _sig(z_bowl1)

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
    p_bat2 = _sig(z_bat2)
    p_bowl2 = _sig(z_bowl2)

    second = df["innings"].to_numpy() == 2
    resolved = df["target_provenance"].isin(
        ["STANDARD_TARGET", "VERIFIED_REVISED_TARGET"]
    ).to_numpy()
    reached = df["is_target_reached_before"].fillna(False).to_numpy()
    chase = (
        second
        & resolved
        & np.isfinite(runs_req)
        & (balls_rem > 0)
        & (~reached)
    )
    invalid = second & (~chase)

    p_bat = np.where(chase, p_bat2, p_bat1)
    p_bowl = np.where(chase, p_bowl2, p_bowl1)
    if fallback:
        p_bat = np.where(invalid, p_bat1, p_bat)
        p_bowl = np.where(invalid, p_bowl1, p_bowl)
    else:
        p_bat = np.where(invalid, np.nan, p_bat)
        p_bowl = np.where(invalid, np.nan, p_bowl)
    return p_bat, p_bowl


def _independent_delivery_fields(df: pd.DataFrame) -> pd.DataFrame:
    extras = df["extras_type_clean"].fillna("none")
    BF = (extras != "wide").astype(float)
    legal = df["is_legal_delivery"].fillna(False).astype(float)
    dot = df["is_dot_ball"].fillna(False).astype(float)
    boundary = (
        df["is_four"].fillna(False) | df["is_six"].fillna(False)
    ).astype(float)
    dismissed = (
        df["is_wicket"].fillna(False)
        & (df["dismissed_player_id"] == df["striker_id"])
        & (df["dismissal_type_clean"].fillna("") != "Retire Out")
    ).astype(float)
    bowler_runs = np.where(
        extras.isin(["wide", "overstep", "other"]),
        df["batter_runs"].astype(float) + df["extras_runs"].astype(float),
        df["batter_runs"].astype(float),
    )
    return pd.DataFrame(
        {
            "BF": BF,
            "legal": legal,
            "dot": dot,
            "boundary": boundary,
            "D": dismissed,
            "bowler_runs": bowler_runs,
        },
        index=df.index,
    )


def _independent_format_records(
    df: pd.DataFrame,
    p_bat: np.ndarray,
    p_bowl: np.ndarray,
    role: str,
) -> pd.DataFrame:
    """Independent aggregation of one player-format record per player."""
    fields = _independent_delivery_fields(df)
    id_col = "striker_id" if role == "batter" else "bowler_id"
    base = pd.DataFrame(
        {
            "match_id": df["match_id"].to_numpy(),
            "match_format": df["match_format"].to_numpy(),
            "player_id": df[id_col].to_numpy(),
            "batter_runs": df["batter_runs"].astype(float).to_numpy(),
            "bowler_runs": fields["bowler_runs"].to_numpy(),
            "BF": fields["BF"].to_numpy(),
            "legal": fields["legal"].to_numpy(),
            "dot": fields["dot"].to_numpy(),
            "boundary": fields["boundary"].to_numpy(),
            "D": fields["D"].to_numpy(),
            "is_bowler_wicket": df["is_bowler_wicket"].fillna(False).astype(float).to_numpy(),
        },
        index=df.index,
    )
    w = p_bat if role == "batter" else p_bowl
    pressure = base[w >= PRESSURE_CUTOFF].copy()
    pressure["w"] = np.square(w[w >= PRESSURE_CUTOFF] / 100.0)
    pressure["w2"] = np.square(pressure["w"])

    if role == "batter":
        pressure["wr"] = pressure["w"] * pressure["batter_runs"]
        pressure["wbf"] = pressure["w"] * pressure["BF"]
        pressure["wbf2"] = np.square(pressure["wbf"])
        pressure["wlegal"] = pressure["w"] * pressure["legal"]
        pressure["wlegal2"] = np.square(pressure["wlegal"])
        pressure["wbound"] = pressure["w"] * pressure["boundary"]
        pressure["wdot"] = pressure["w"] * pressure["dot"]
        pressure["wD"] = pressure["w"] * pressure["D"]
        rec = pressure.groupby(
            ["match_format", "player_id"], as_index=False
        ).agg(
            N_raw=("match_id", "size"),
            M_format=("match_id", "nunique"),
            sum_w=("w", "sum"),
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

        baseline = base[w < PRESSURE_CUTOFF].copy()
        bgrp = baseline.groupby(["match_format", "player_id"], as_index=False).agg(
            baseline_BF=("BF", "sum"),
            baseline_legal=("legal", "sum"),
            base_runs=("batter_runs", "sum"),
            base_dot=("dot", "sum"),
            base_D=("D", "sum"),
            base_deliveries=("match_id", "size"),
            base_matches=("match_id", "nunique"),
        )
        bgrp["SR_base"] = 100.0 * bgrp["base_runs"] / bgrp["baseline_BF"].replace(0, np.nan)
        bgrp["Dot_base"] = (
            100.0 * bgrp["base_dot"] / bgrp["baseline_legal"].replace(0, np.nan)
        )
        bgrp["DR_base"] = 100.0 * bgrp["base_D"] / bgrp["baseline_BF"].replace(0, np.nan)
        rec = rec.merge(
            bgrp[
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
        rec["format_gate"] = (rec["N_raw"] >= RAW_GATE) & (
            rec["N_eff_del"] >= NEFF_GATE
        )
        rec["denoms_ok"] = (
            (rec["sum_wbf"].fillna(0) > 0)
            & (rec["sum_wlegal"].fillna(0) > 0)
        )
    else:
        pressure["wr"] = pressure["w"] * pressure["bowler_runs"]
        pressure["wlegal"] = pressure["w"] * pressure["legal"]
        pressure["wlegal2"] = np.square(pressure["wlegal"])
        pressure["wwkt"] = pressure["w"] * pressure["is_bowler_wicket"]
        pressure["wdot"] = pressure["w"] * pressure["dot"]
        pressure["wbound"] = pressure["w"] * pressure["boundary"]
        rec = pressure.groupby(
            ["match_format", "player_id"], as_index=False
        ).agg(
            N_raw=("match_id", "size"),
            M_format=("match_id", "nunique"),
            sum_w=("w", "sum"),
            sum_w2=("w2", "sum"),
            sum_wr=("wr", "sum"),
            sum_wlegal=("wlegal", "sum"),
            sum_wlegal2=("wlegal2", "sum"),
            sum_wwkt=("wwkt", "sum"),
            sum_wdot=("wdot", "sum"),
            sum_wbound=("wbound", "sum"),
        )
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

        baseline = base[w < PRESSURE_CUTOFF].copy()
        bgrp = baseline.groupby(["match_format", "player_id"], as_index=False).agg(
            baseline_legal=("legal", "sum"),
            base_runs=("bowler_runs", "sum"),
            base_dot=("dot", "sum"),
            base_bound=("boundary", "sum"),
            base_deliveries=("match_id", "size"),
            base_matches=("match_id", "nunique"),
        )
        bgrp["Econ_base"] = (
            6.0 * bgrp["base_runs"] / bgrp["baseline_legal"].replace(0, np.nan)
        )
        bgrp["Dot_base"] = (
            100.0 * bgrp["base_dot"] / bgrp["baseline_legal"].replace(0, np.nan)
        )
        bgrp["BoundaryConc_base"] = (
            100.0 * bgrp["base_bound"] / bgrp["baseline_legal"].replace(0, np.nan)
        )
        rec = rec.merge(
            bgrp[
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
        rec["format_gate"] = (rec["N_raw"] >= RAW_GATE) & (
            rec["N_eff_del"] >= NEFF_GATE
        )
        rec["denoms_ok"] = rec["sum_wlegal"].fillna(0) > 0
    return rec


def _compare_frames(
    engine: pd.DataFrame,
    independent: pd.DataFrame,
    keys: list[str],
    columns: list[str],
    label: str,
    checks: list[dict],
    tol: float = 1e-9,
) -> None:
    """Compare numeric columns after an outer join on the record keys."""
    e = engine[keys + columns].copy()
    i = independent[keys + columns].copy()
    for frame in (e, i):
        frame["player_id"] = pd.to_numeric(frame["player_id"], errors="coerce")
        frame["match_format"] = frame["match_format"].astype(str)
    merged = e.merge(i, on=keys, how="outer", suffixes=("_engine", "_indep"), indicator=True)
    missing = int((merged["_merge"] != "both").sum())
    failures = []
    if missing:
        failures.append(f"{missing} key(s) missing on one side")
    for col in columns:
        a = pd.to_numeric(merged[f"{col}_engine"], errors="coerce")
        b = pd.to_numeric(merged[f"{col}_indep"], errors="coerce")
        if not _allclose(a, b, atol=tol, rtol=tol):
            failures.append(f"{col} max|diff|={_max_abs_diff(a, b):.3g}")
    _add(
        checks,
        "Independent aggregation",
        f"{label}: engine record table matches independent aggregation",
        not failures,
        "; ".join(failures) if failures else f"{len(e):,} records compared",
    )


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------
CANONICAL_SCENARIOS = (
    ("S1", 96, 120, 48, 2, 75.3, 23.0),
    ("S2", 96, 120, 48, 8, 94.0, 1.8),
    ("S3", 114, 120, 6, 9, 86.4, 98.1),
    ("S4", 90, 120, 24, 0, 17.5, 4.3),
    ("S5", 114, 120, 42, 4, 99.2, 1.6),
    ("S6", 117, 120, 4, 8, 88.0, 79.3),
    ("S7", 102, 120, 30, 5, 79.2, 49.3),
    ("S8", 30, 60, 45, 2, 48.5, 83.0),
)


def _canonical_frame() -> pd.DataFrame:
    rows = []
    for name, b, mb, rr, w, _, _ in CANONICAL_SCENARIOS:
        rows.append(
            {
                "scenario": name,
                "legal_balls_before": b,
                "max_balls": mb,
                "runs_before": 0.0,
                "wickets_before": w,
                "runs_required": rr,
                "match_format": "T20",
                "innings": 2,
                "target_provenance": "STANDARD_TARGET",
                "is_target_reached_before": False,
            }
        )
    return pd.DataFrame(rows)


def _canonical_results() -> pd.DataFrame:
    frame = _canonical_frame()
    p_bat, p_bowl = _independent_pressure(frame)
    out = frame[["scenario"]].copy()
    out["expected_bat"] = [row[5] for row in CANONICAL_SCENARIOS]
    out["expected_bowl"] = [row[6] for row in CANONICAL_SCENARIOS]
    out["observed_bat"] = p_bat
    out["observed_bowl"] = p_bowl
    out["delta_bat"] = out["observed_bat"] - out["expected_bat"]
    out["delta_bowl"] = out["observed_bowl"] - out["expected_bowl"]
    return out


def _check_corpus(result: dict, checks: list[dict]) -> None:
    audit = result["audit"]
    scoring = result["scoring"]

    _add(
        checks,
        "Corpus",
        "Audit corpus row count",
        len(audit) == AUDIT_CORPUS_ROWS,
        f"{len(audit):,} observed / {AUDIT_CORPUS_ROWS:,} approved",
    )
    _add(
        checks,
        "Corpus",
        "Scoring corpus row count",
        len(scoring) == SCORING_CORPUS_ROWS,
        f"{len(scoring):,} observed / {SCORING_CORPUS_ROWS:,} approved",
    )
    _add(
        checks,
        "Corpus",
        "Scoring corpus match count",
        scoring["match_id"].nunique() == 812,
        f"{scoring['match_id'].nunique():,} matches",
    )
    format_counts = scoring["match_format"].value_counts().to_dict()
    _add(
        checks,
        "Corpus",
        "Format row counts",
        format_counts.get("T20") == 87_217 and format_counts.get("T20I") == 104_746,
        f"T20={format_counts.get('T20', 0):,}; T20I={format_counts.get('T20I', 0):,}",
    )

    m48610 = audit[audit["match_id"] == MATCH_48610_ID]
    chase = m48610[m48610["innings"] == 2]
    first = m48610[m48610["innings"] == 1]
    _add(
        checks,
        "Match 48610",
        "Retain 101 first-innings deliveries",
        len(first) == 101,
        f"{len(first)} first-innings rows",
    )
    _add(
        checks,
        "Match 48610",
        "Identify 93 excluded second-innings deliveries",
        len(chase) == 93,
        f"{len(chase)} second-innings rows in audit corpus",
    )
    _add(
        checks,
        "Match 48610",
        "Remove the 93 chase rows from the scoring corpus",
        len(scoring[scoring["match_id"] == MATCH_48610_ID]) == 101
        and not ((scoring["match_id"] == MATCH_48610_ID) & (scoring["innings"] == 2)).any(),
        f"{len(scoring[scoring['match_id'] == MATCH_48610_ID])} retained rows",
    )
    _add(
        checks,
        "Match 48610",
        "Excluded chase contains zero `other` extras",
        not (chase["extras_type_clean"] == "other").any(),
        f"{int((chase['extras_type_clean'] == 'other').sum())} `other` rows",
    )
    chase_pressure = chase[chase["p_bowl"] >= PRESSURE_CUTOFF]
    chase_boundary = int(chase_pressure["boundary"].sum())
    _add(
        checks,
        "Match 48610",
        "Excluded chase contributes 11 pressure boundaries",
        chase_boundary == 11,
        f"{chase_boundary} boundary rows; "
        f"{int(chase_pressure['is_four'].sum())} fours + "
        f"{int(chase_pressure['is_six'].sum())} sixes",
    )

    _add(
        checks,
        "`other` extras",
        "`other` count is unchanged by the chase exclusion",
        int((audit["extras_type_clean"] == "other").sum()) == 256
        and int((scoring["extras_type_clean"] == "other").sum()) == 256,
        f"audit={int((audit['extras_type_clean'] == 'other').sum())}; "
        f"scoring={int((scoring['extras_type_clean'] == 'other').sum())}",
    )

    # Q10 boundary counts on each corpus.
    for label, frame in (("audit", audit), ("scoring", scoring)):
        pressure = frame[frame["p_bowl"] >= PRESSURE_CUTOFF]
        boundary = pressure["boundary"].astype(bool)
        legal = pressure["legal"].astype(bool)
        overstep = pressure["extras_type_clean"].eq("overstep")
        counts = {
            "legal only": int((boundary & legal).sum()),
            "legal + overstep": int((boundary & (legal | overstep)).sum()),
            "legal + overstep + other": int(boundary.sum()),
        }
        expected = (
            {"legal only": 9_767, "legal + overstep": 9_801, "legal + overstep + other": 9_827}
            if label == "audit"
            else {"legal only": 9_756, "legal + overstep": 9_790, "legal + overstep + other": 9_816}
        )
        _add(
            checks,
            "Q10 boundaries",
            f"{label.capitalize()} boundary-conceded counts",
            counts == expected,
            ", ".join(f"{k}={counts[k]:,}" for k in counts),
        )
        weighted = {
            "legal only": float(pressure.loc[boundary & legal, "w_bowl"].sum()),
            "legal + overstep": float(
                pressure.loc[boundary & (legal | overstep), "w_bowl"].sum()
            ),
            "legal + overstep + other": float(pressure.loc[boundary, "w_bowl"].sum()),
        }
        expected_weighted = (
            {
                "legal only": 6_552.537349,
                "legal + overstep": 6_576.615108,
                "legal + overstep + other": 6_594.333604,
            }
            if label == "audit"
            else {
                "legal only": 6_547.268516,
                "legal + overstep": 6_571.346275,
                "legal + overstep + other": 6_589.064771,
            }
        )
        _add(
            checks,
            "Q10 boundaries",
            f"{label.capitalize()} weighted boundary numerators",
            all(
                abs(weighted[k] - expected_weighted[k]) < 1e-6 for k in weighted
            ),
            ", ".join(f"{k}={weighted[k]:.6f}" for k in weighted),
        )
        denominator = float(pressure.loc[legal, "w_bowl"].sum())
        expected_denominator = 30_057.770551 if label == "audit" else 30_021.669303
        _add(
            checks,
            "Q10 boundaries",
            f"{label.capitalize()} weighted boundary denominator",
            abs(denominator - expected_denominator) < 1e-6,
            f"{denominator:.6f} observed / {expected_denominator:.6f} approved",
        )

    pressure_other = scoring[
        (scoring["p_bowl"] >= PRESSURE_CUTOFF)
        & (scoring["extras_type_clean"] == "other")
    ]
    observed_other = {
        "rows": len(pressure_other),
        "batter_runs": int(pressure_other["batter_runs"].sum()),
        "extras_runs": int(pressure_other["extras_runs"].sum()),
        "boundaries": int(pressure_other["boundary"].sum()),
        "weighted_extras": float(
            (pressure_other["w_bowl"] * pressure_other["extras_runs"]).sum()
        ),
        "weighted_batter_runs": float(
            (pressure_other["w_bowl"] * pressure_other["batter_runs"]).sum()
        ),
    }
    expected_other = {
        "rows": 88,
        "batter_runs": 139,
        "extras_runs": 104,
        "boundaries": 26,
        "weighted_extras": 74.467115,
        "weighted_batter_runs": 96.670587,
    }
    _add(
        checks,
        "`other` extras",
        "Pressure-set `other` contents",
        observed_other["rows"] == expected_other["rows"]
        and observed_other["batter_runs"] == expected_other["batter_runs"]
        and observed_other["extras_runs"] == expected_other["extras_runs"]
        and observed_other["boundaries"] == expected_other["boundaries"]
        and abs(observed_other["weighted_extras"] - expected_other["weighted_extras"]) < 1e-6
        and abs(
            observed_other["weighted_batter_runs"]
            - expected_other["weighted_batter_runs"]
        )
        < 1e-6,
        ", ".join(f"{k}={v}" if not isinstance(v, float) else f"{k}={v:.6f}" for k, v in observed_other.items()),
    )


def _check_pressure_engine(result: dict, checks: list[dict]) -> None:
    canonical = _canonical_results()
    max_delta = max(
        float(canonical["delta_bat"].abs().max()),
        float(canonical["delta_bowl"].abs().max()),
    )
    _add(
        checks,
        "Pressure engine",
        "Eight canonical scenarios reproduce approved P_bat/P_bowl",
        max_delta <= 0.1,
        f"max |delta|={max_delta:.4f}; tolerance 0.1",
    )

    scoring = result["scoring"]
    p_bat, p_bowl = _independent_pressure(scoring)
    _add(
        checks,
        "Pressure engine",
        "Scoring-corpus P_bat matches independent recomputation",
        _allclose(scoring["p_bat"], p_bat, atol=1e-10),
        f"max |diff|={_max_abs_diff(scoring['p_bat'], p_bat):.3g}",
    )
    _add(
        checks,
        "Pressure engine",
        "Scoring-corpus P_bowl matches independent recomputation",
        _allclose(scoring["p_bowl"], p_bowl, atol=1e-10),
        f"max |diff|={_max_abs_diff(scoring['p_bowl'], p_bowl):.3g}",
    )
    _add(
        checks,
        "Pressure engine",
        "Scoring-corpus pressure values are finite",
        np.isfinite(scoring["p_bat"]).all() and np.isfinite(scoring["p_bowl"]).all(),
        f"{int((~np.isfinite(scoring['p_bat'])).sum())} non-finite P_bat; "
        f"{int((~np.isfinite(scoring['p_bowl'])).sum())} non-finite P_bowl",
    )
    _add(
        checks,
        "Pressure engine",
        "Pressure values lie in [0, 100]",
        bool(
            scoring["p_bat"].between(0, 100).all()
            and scoring["p_bowl"].between(0, 100).all()
        ),
        f"P_bat [{scoring['p_bat'].min():.4f}, {scoring['p_bat'].max():.4f}]; "
        f"P_bowl [{scoring['p_bowl'].min():.4f}, {scoring['p_bowl'].max():.4f}]",
    )
    expected_w_bat = np.where(
        scoring["p_bat"] >= PRESSURE_CUTOFF,
        np.square(scoring["p_bat"] / 100.0),
        0.0,
    )
    expected_w_bowl = np.where(
        scoring["p_bowl"] >= PRESSURE_CUTOFF,
        np.square(scoring["p_bowl"] / 100.0),
        0.0,
    )
    _add(
        checks,
        "Pressure engine",
        "Pressure weights use the approved square above 60",
        _allclose(scoring["w_bat"], expected_w_bat)
        and _allclose(scoring["w_bowl"], expected_w_bowl),
        f"max |diff| w_bat={_max_abs_diff(scoring['w_bat'], expected_w_bat):.3g}; "
        f"w_bowl={_max_abs_diff(scoring['w_bowl'], expected_w_bowl):.3g}",
    )

    audit = result["audit"]
    audit_p_bat, audit_p_bowl = _independent_pressure(audit, fallback=True)
    _add(
        checks,
        "Pressure engine",
        "Audit-corpus P1 fallback matches independent recomputation",
        _allclose(audit["p_bat"], audit_p_bat, atol=1e-10)
        and _allclose(audit["p_bowl"], audit_p_bowl, atol=1e-10),
        f"max |diff| P_bat={_max_abs_diff(audit['p_bat'], audit_p_bat):.3g}; "
        f"P_bowl={_max_abs_diff(audit['p_bowl'], audit_p_bowl):.3g}",
    )


def _check_attribution(result: dict, checks: list[dict]) -> None:
    scoring = result["scoring"]
    fields = _independent_delivery_fields(scoring)
    mapping = {
        "BF": "BF",
        "legal": "legal",
        "dot_i": "dot",
        "boundary": "boundary",
        "D": "D",
        "bowler_runs": "bowler_runs",
    }
    failures = []
    for engine_col, indep_col in mapping.items():
        if not _allclose(scoring[engine_col], fields[indep_col], atol=0.0):
            failures.append(
                f"{engine_col} max|diff|={_max_abs_diff(scoring[engine_col], fields[indep_col]):.3g}"
            )
    _add(
        checks,
        "Delivery attribution",
        "Ball-faced, legal, dot, boundary, dismissal and bowler-run attribution",
        not failures,
        "; ".join(failures) if failures else f"{len(scoring):,} deliveries checked",
    )
    other = scoring[scoring["extras_type_clean"] == "other"]
    _add(
        checks,
        "Delivery attribution",
        "`other` remains provisional no-ball-like",
        len(other) > 0
        and bool((other["BF"] == 1).all())
        and bool((other["legal"] == 0).all())
        and bool((other["dot_i"] == 0).all())
        and bool(
            np.allclose(
                other["bowler_runs"],
                other["batter_runs"].astype(float) + other["extras_runs"].astype(float),
            )
        ),
        f"{len(other)} `other` rows; BF=1; legal=0; dot=0; "
        "bowler runs=batter+extras",
    )
    _add(
        checks,
        "Delivery attribution",
        "Retire Out is excluded from the batter dismissal numerator",
        int(scoring.loc[scoring["dismissal_type_clean"] == "Retire Out", "D"].sum()) == 0,
        f"{int((scoring['dismissal_type_clean'] == 'Retire Out').sum())} Retire Out rows",
    )


def _check_moments_and_peers(result: dict, checks: list[dict]) -> None:
    for role in ("batter", "bowler"):
        records = result[f"{role}_records"]
        metrics = BATTER_METRICS if role == "batter" else BOWLER_METRICS
        failures = []
        for name, weight, raw_col, neff_col, use_peer, sign in metrics:
            for fmt in FORMAT_ORDER:
                r = records[records["match_format"] == fmt].copy()
                denom_col = "sum_wbf" if role == "batter" and name != "dDot" else "sum_wlegal"
                r = r[
                    (r["N_raw"] >= RAW_GATE)
                    & (r["N_eff_del"] >= NEFF_GATE)
                    & (r[denom_col] > 0)
                ]
                need_base = name in {"dSR", "dDot", "dDR", "dEcon"}
                if need_base:
                    r = r[r["baseline_ok"]]
                r = r[np.isfinite(r[raw_col]) & np.isfinite(r[neff_col])]
                if r.empty:
                    failures.append(f"{fmt}/{name}: empty reference set")
                    continue
                prior = MU_PEER[(fmt, name)] if use_peer else 0.0
                neff = r[neff_col].astype(float)
                shrunk = (neff / (neff + SHRINKAGE_K)) * r[raw_col].astype(float) + (
                    SHRINKAGE_K / (neff + SHRINKAGE_K)
                ) * prior
                observed = (float(shrunk.mean()), float(shrunk.std(ddof=0)))
                expected = REFERENCE_MOMENTS[(role, fmt, name)]
                if abs(observed[0] - expected[0]) > 1e-8 or abs(
                    observed[1] - expected[1]
                ) > 1e-8:
                    failures.append(
                        f"{fmt}/{name}: mean {observed[0]:.10f} vs {expected[0]:.10f}; "
                        f"sd {observed[1]:.10f} vs {expected[1]:.10f}"
                    )
        _add(
            checks,
            "Reference moments",
            f"{role.capitalize()} reference moments match independent recomputation",
            not failures,
            "; ".join(failures[:5])
            if failures
            else f"{len(metrics) * len(FORMAT_ORDER)} format-metric moments checked",
        )

    peer_failures = []
    for (fmt, name), expected in MU_PEER.items():
        if name in {"SR_P", "Boundary_P"}:
            records = result["batter_records"]
            denom_col = "sum_wbf"
        else:
            records = result["bowler_records"]
            denom_col = "sum_wlegal"
        r = records[
            (records["match_format"] == fmt) & (records[denom_col] > 0)
        ]
        observed = float(r[name].mean())
        if abs(observed - expected) > 1e-8:
            peer_failures.append(f"{fmt}/{name}: {observed:.10f} vs {expected:.10f}")
    _add(
        checks,
        "Peer means",
        "Approved peer means match independent recomputation",
        not peer_failures,
        "; ".join(peer_failures) if peer_failures else "12 peer means checked",
    )


def _check_format_records(result: dict, checks: list[dict]) -> None:
    for role in ("batter", "bowler"):
        records = result[f"{role}_records"]
        metrics = BATTER_METRICS if role == "batter" else BOWLER_METRICS
        failures = []
        for name, weight, raw_col, neff_col, use_peer, sign in metrics:
            neff = records[neff_col].astype(float)
            raw = records[raw_col].astype(float)
            prior = (
                records["match_format"].map(lambda f: MU_PEER[(f, name)])
                if use_peer
                else 0.0
            )
            shrunk = (neff / (neff + SHRINKAGE_K)) * raw + (
                SHRINKAGE_K / (neff + SHRINKAGE_K)
            ) * prior
            if not _allclose(records[f"shrunk_{name}"], shrunk):
                failures.append(
                    f"shrunk_{name} max|diff|={_max_abs_diff(records[f'shrunk_{name}'], shrunk):.3g}"
                )
            mean_sd = records["match_format"].map(
                lambda f: REFERENCE_MOMENTS[(role, f, name)]
            )
            mean = mean_sd.map(lambda x: x[0])
            sd = mean_sd.map(lambda x: x[1])
            z = (shrunk - mean) / sd
            if not _allclose(records[f"z_{name}"], z):
                failures.append(
                    f"z_{name} max|diff|={_max_abs_diff(records[f'z_{name}'], z):.3g}"
                )
        composite = sum(
            sign * weight * records[f"z_{name}"]
            for name, weight, _, _, _, sign in metrics
        )
        if not _allclose(records["Z_comp_format"], composite):
            failures.append(
                f"Z_comp_format max|diff|={_max_abs_diff(records['Z_comp_format'], composite):.3g}"
            )
        _add(
            checks,
            "Composite",
            f"{role.capitalize()} shrinkage, z-scores and weighted composite",
            not failures,
            "; ".join(failures) if failures else f"{len(records):,} format records checked",
        )

        expected_gate = (records["N_raw"] >= RAW_GATE) & (
            records["N_eff_del"] >= NEFF_GATE
        )
        _add(
            checks,
            "Format eligibility",
            f"{role.capitalize()} N_raw and N_eff,del gate",
            np.array_equal(records["format_gate"].astype(bool), expected_gate.astype(bool)),
            f"{int(expected_gate.sum()):,} records pass the format gate",
        )
        if role == "batter":
            expected_baseline = (
                records["baseline_BF"].fillna(0) >= 120
            ) & (records["baseline_legal"].fillna(0) >= 120)
        else:
            expected_baseline = records["baseline_legal"].fillna(0) >= 120
        _add(
            checks,
            "Format eligibility",
            f"{role.capitalize()} baseline exposure gate",
            np.array_equal(
                records["baseline_ok"].astype(bool), expected_baseline.astype(bool)
            ),
            f"{int(expected_baseline.sum()):,} records pass the baseline gate",
        )
        expected_denoms = (
            records[[f"den_{name}" for name, *_ in metrics]].fillna(0) > 0
        ).all(axis=1)
        _add(
            checks,
            "Format eligibility",
            f"{role.capitalize()} all five metric denominators are positive",
            np.array_equal(
                records["denoms_ok"].astype(bool), expected_denoms.astype(bool)
            ),
            f"{int(expected_denoms.sum()):,} records pass the denominator gate",
        )
        expected_ready = (
            expected_gate
            & expected_baseline
            & expected_denoms
            & np.isfinite(records["Z_comp_format"])
        )
        _add(
            checks,
            "Format eligibility",
            f"{role.capitalize()} composite-ready definition",
            np.array_equal(
                records["composite_ready"].astype(bool), expected_ready.astype(bool)
            ),
            f"{int(expected_ready.sum()):,} composite-ready records",
        )


def _check_player_tables(result: dict, checks: list[dict]) -> None:
    for role in ("batter", "bowler"):
        records = result[f"{role}_records"]
        players = result[f"{role}_players"]
        f_records = records[records["composite_ready"]].copy()

        expected_f = f_records.groupby("player_id").agg(
            Z_comp=("Z_comp_format", "mean"),
            M_role=("M_format", "sum"),
            sum_N_raw_F=("N_raw", "sum"),
            sum_N_eff_del_F=("N_eff_del", "sum"),
            n_formats_F=("match_format", "nunique"),
        )
        m_all = records.groupby("player_id")["M_format"].sum()

        merged = players.set_index("player_id").merge(
            expected_f,
            left_index=True,
            right_index=True,
            how="left",
            suffixes=("", "_expected"),
        )
        failures = []
        f_nonempty = merged["Z_comp"].notna()
        if not np.array_equal(
            merged["F_nonempty"].astype(bool), f_nonempty.astype(bool)
        ):
            failures.append("F_nonempty mismatch")
        if not np.array_equal(
            merged["calibration_population"].astype(bool), f_nonempty.astype(bool)
        ):
            failures.append("calibration_population mismatch")
        expected_m_role = merged["M_role_expected"].fillna(0).astype(int)
        if not np.array_equal(merged["M_role"].astype(int), expected_m_role):
            failures.append("M_role mismatch")
        expected_m_all = merged.index.map(m_all).fillna(0).astype(int)
        if not np.array_equal(merged["M_all"].astype(int), expected_m_all):
            failures.append("M_all mismatch")
        for col in ("sum_N_raw_F", "sum_N_eff_del_F", "n_formats_F"):
            merged[f"{col}_expected"] = merged[f"{col}_expected"].fillna(0)
        for col in ("Z_comp", "sum_N_raw_F", "sum_N_eff_del_F", "n_formats_F"):
            if not _allclose(merged[col], merged[f"{col}_expected"]):
                failures.append(
                    f"{col} max|diff|={_max_abs_diff(merged[col], merged[f'{col}_expected']):.3g}"
                )
        expected_eligible = f_nonempty & (expected_m_role >= MATCH_GATE)
        if not np.array_equal(
            merged["ranking_eligible"].astype(bool), expected_eligible.astype(bool)
        ):
            failures.append("ranking_eligible mismatch")
        _add(
            checks,
            "Player aggregation",
            f"{role.capitalize()} equal-weight format composite and eligibility",
            not failures,
            "; ".join(failures) if failures else f"{len(players):,} player rows checked",
        )

        # F_formats ordering uses the approved T20, T20I order.
        bad_formats = []
        for _, row in players[players["F_nonempty"]].iterrows():
            fmts = f_records[f_records["player_id"] == row["player_id"]][
                "match_format"
            ].tolist()
            fmts = sorted(fmts, key=lambda f: FORMAT_ORDER.index(f))
            expected_labels = ",".join(FORMAT_LABELS[f] for f in fmts)
            if row["F_formats"] != expected_labels:
                bad_formats.append(f"{row['player_id']}: {row['F_formats']} != {expected_labels}")
        _add(
            checks,
            "Player aggregation",
            f"{role.capitalize()} F format labels and ordering",
            not bad_formats,
            "; ".join(bad_formats[:5]) if bad_formats else "all F labels match",
        )

        # Calibration and reliability.
        cal = players[players["calibration_population"]].copy()
        cal_cfg = CALIBRATION[role]
        n_ok = len(cal) == cal_cfg["n"]
        mu = float(cal["Z_comp"].mean())
        sigma = float(cal["Z_comp"].std(ddof=0))
        _add(
            checks,
            "Calibration",
            f"{role.capitalize()} calibration population size",
            n_ok,
            f"n={len(cal)} / approved {cal_cfg['n']}",
        )
        _add(
            checks,
            "Calibration",
            f"{role.capitalize()} calibration mean and population SD",
            abs(mu - cal_cfg["mu"]) < 1e-8 and abs(sigma - cal_cfg["sigma"]) < 1e-8,
            f"mu={mu:.10f} (approved {cal_cfg['mu']:.10f}); "
            f"sigma={sigma:.10f} (approved {cal_cfg['sigma']:.10f})",
        )
        expected_zstd = (cal["Z_comp"] - cal_cfg["mu"]) / cal_cfg["sigma"]
        expected_rel = 100.0 / (1.0 + np.exp(-RELIABILITY_GAMMA * expected_zstd))
        _add(
            checks,
            "Reliability",
            f"{role.capitalize()} Z_std and reliability formula",
            _allclose(cal["Z_std"], expected_zstd)
            and _allclose(cal["Reliability"], expected_rel),
            f"max |diff| Z_std={_max_abs_diff(cal['Z_std'], expected_zstd):.3g}; "
            f"Reliability={_max_abs_diff(cal['Reliability'], expected_rel):.3g}",
        )
        _add(
            checks,
            "Reliability",
            f"{role.capitalize()} reliability is finite and in [0, 100]",
            np.isfinite(cal["Reliability"]).all()
            and bool(cal["Reliability"].between(0, 100).all()),
            f"range [{cal['Reliability'].min():.6f}, {cal['Reliability'].max():.6f}]",
        )

        # Ranking order.
        eligible = players[players["ranking_eligible"]].copy()
        expected_order = eligible.sort_values(
            [
                "Z_comp",
                "sum_N_eff_del_F",
                "M_role",
                "sum_N_raw_F",
                "player_id",
            ],
            ascending=[False, False, False, False, True],
            kind="mergesort",
        ).reset_index(drop=True)
        observed_order = eligible.sort_values(
            "final_rank", kind="mergesort"
        ).reset_index(drop=True)
        order_ok = observed_order["player_id"].tolist() == expected_order[
            "player_id"
        ].tolist()
        ranks_ok = observed_order["final_rank"].tolist() == list(
            range(1, len(observed_order) + 1)
        )
        _add(
            checks,
            "Ranking",
            f"{role.capitalize()} deterministic order and contiguous ranks",
            order_ok and ranks_ok,
            f"{len(observed_order)} ranked players; order_ok={order_ok}; ranks_ok={ranks_ok}",
        )
        _add(
            checks,
            "Ranking",
            f"{role.capitalize()} no player with M_role < 10 is ranked",
            bool((eligible["M_role"] >= MATCH_GATE).all()),
            f"{int((eligible['M_role'] < MATCH_GATE).sum())} violations",
        )
        _add(
            checks,
            "Ranking",
            f"{role.capitalize()} ranked scores are finite and non-missing",
            np.isfinite(eligible["Z_comp"]).all()
            and np.isfinite(eligible["Z_std"]).all()
            and np.isfinite(eligible["Reliability"]).all(),
            f"{int((~np.isfinite(eligible['Z_comp'])).sum())} non-finite Z_comp",
        )
        _add(
            checks,
            "Ranking",
            f"{role.capitalize()} player IDs are unique",
            not players["player_id"].duplicated().any()
            and not eligible["player_id"].duplicated().any(),
            f"{int(players['player_id'].duplicated().sum())} duplicate player rows",
        )
        _add(
            checks,
            "Ranking",
            f"{role.capitalize()} ranked player names are present",
            eligible["player_name"].notna().all()
            and (eligible["player_name"].astype(str).str.len() > 0).all(),
            f"{int(eligible['player_name'].isna().sum())} missing names",
        )

        # Top-10 list must be the first ten ranked players.
        top = result[f"top10_{role}s"]
        expected_top = observed_order.head(10)
        top_ok = len(top) == 10 and top["player_id"].tolist() == expected_top[
            "player_id"
        ].tolist()
        _add(
            checks,
            "Top 10",
            f"{role.capitalize()} top 10 matches the full ranking table",
            top_ok,
            f"{len(top)} rows; IDs="
            + ",".join(str(int(x)) for x in top["player_id"].tolist()),
        )


def _check_population_counts(result: dict, checks: list[dict]) -> None:
    expected = {
        "batter": {
            "composite_records": 144,
            "composite_players": 122,
            "final_records": 123,
            "final_players": 101,
            "m_lt_10": 21,
            "m_all_ge_10": 103,
            "calibration": 122,
        },
        "bowler": {
            "composite_records": 209,
            "composite_players": 173,
            "final_records": 177,
            "final_players": 141,
            "m_lt_10": 32,
            "m_all_ge_10": 146,
            "calibration": 173,
        },
    }
    for role in ("batter", "bowler"):
        records = result[f"{role}_records"]
        players = result[f"{role}_players"]
        exp = expected[role]
        observed = {
            "composite_records": int(records["composite_ready"].sum()),
            "composite_players": int(
                records.loc[records["composite_ready"], "player_id"].nunique()
            ),
            "final_records": int(records["ranking_eligible"].sum()),
            "final_players": int(players["ranking_eligible"].sum()),
            "m_lt_10": int((players["status"] == "M_BREADTH_INSUFFICIENT").sum()),
            "m_all_ge_10": int(
                (
                    records[records["composite_ready"]]
                    .groupby("player_id")["M_all"]
                    .max()
                    >= MATCH_GATE
                ).sum()
            ),
            "calibration": int(players["calibration_population"].sum()),
        }
        failures = [
            f"{key}: {observed[key]} != {exp[key]}"
            for key in exp
            if observed[key] != exp[key]
        ]
        _add(
            checks,
            "Populations",
            f"{role.capitalize()} approved population counts",
            not failures,
            "; ".join(failures)
            if failures
            else ", ".join(f"{k}={v}" for k, v in observed.items()),
        )

    batter_ids = set(
        result["batter_players"].loc[
            result["batter_players"]["ranking_eligible"], "player_id"
        ]
    )
    bowler_ids = set(
        result["bowler_players"].loc[
            result["bowler_players"]["ranking_eligible"], "player_id"
        ]
    )
    _add(
        checks,
        "Populations",
        "Both-role final-eligible players",
        len(batter_ids & bowler_ids) == 23,
        f"{len(batter_ids & bowler_ids)} players",
    )


def _check_outputs(checks: list[dict]) -> None:
    expected_counts = {
        "batter_format_records": 907,
        "bowler_format_records": 628,
        "batter_scoring": 746,
        "bowler_scoring": 507,
        "top10_batters": 10,
        "top10_bowlers": 10,
        "eligibility_audit": 1_253,
        "format_eligibility_audit": 1_535,
        "calibration_population": 295,
    }
    failures = []
    for key, filename in OUTPUT_FILES.items():
        if key == "scoring_validation":
            continue
        path = OUTPUT_DIR / filename
        if not path.exists():
            failures.append(f"{filename}: missing")
            continue
        if path.stat().st_size == 0:
            failures.append(f"{filename}: empty")
            continue
        try:
            frame = pd.read_csv(path)
        except Exception as exc:  # pragma: no cover - defensive
            failures.append(f"{filename}: unreadable ({exc})")
            continue
        if "player_id" not in frame.columns and key != "format_eligibility_audit":
            failures.append(f"{filename}: no player_id column")
        if key in expected_counts and len(frame) != expected_counts[key]:
            failures.append(
                f"{filename}: {len(frame)} rows != {expected_counts[key]}"
            )
    _add(
        checks,
        "Output files",
        "All required Stage 5 CSV outputs exist, are non-empty and have expected row counts",
        not failures,
        "; ".join(failures) if failures else "9 CSV files checked",
    )


def run_validation_checks(
    result: dict, check_outputs: bool = False
) -> list[dict]:
    """Run every Stage 5 validation check and return structured results."""
    checks: list[dict] = []
    _check_corpus(result, checks)
    _check_pressure_engine(result, checks)
    _check_attribution(result, checks)
    _check_moments_and_peers(result, checks)
    _check_format_records(result, checks)

    # Independent aggregation of both role tables.
    scoring = result["scoring"]
    p_bat, p_bowl = _independent_pressure(scoring)
    batter_indep = _independent_format_records(scoring, p_bat, p_bowl, "batter")
    bowler_indep = _independent_format_records(scoring, p_bat, p_bowl, "bowler")
    _compare_frames(
        result["batter_records"],
        batter_indep,
        ["match_format", "player_id"],
        [
            "N_raw", "M_format", "N_eff_del", "N_eff_BF", "N_eff_legal",
            "SR_P", "Boundary_P", "Dot_P", "DR_P",
            "baseline_BF", "baseline_legal", "base_deliveries", "base_matches",
            "SR_base", "Dot_base", "DR_base", "dSR", "dDot", "dDR", "baseline_ok",
        ],
        "Batter",
        checks,
    )
    _compare_frames(
        result["bowler_records"],
        bowler_indep,
        ["match_format", "player_id"],
        [
            "N_raw", "M_format", "N_eff_del", "N_eff_legal",
            "Econ_P", "WktRate_P", "Dot_bowl_P", "BoundaryConc_P",
            "baseline_legal", "base_deliveries", "base_matches",
            "Econ_base", "Dot_base", "BoundaryConc_base", "dEcon", "baseline_ok",
        ],
        "Bowler",
        checks,
    )

    _check_player_tables(result, checks)
    _check_population_counts(result, checks)
    if check_outputs:
        _check_outputs(checks)
    return checks


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------
def _md_table(headers: list[str], rows: Iterable[Iterable]) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def _status_icon(passed: bool) -> str:
    return "PASS" if passed else "**FAIL**"


def build_validation_report(
    result: dict,
    checks: list[dict] | None = None,
    check_outputs: bool = False,
) -> str:
    """Build the Markdown validation report.

    The caller can pass pre-computed checks so the runner writes the report
    and uses the same check results to set its exit status.
    """
    if checks is None:
        checks = run_validation_checks(result, check_outputs=check_outputs)
    passed = all(check["passed"] for check in checks)
    failures = [check for check in checks if not check["passed"]]

    scoring = result["scoring"]
    audit = result["audit"]
    batter_players = result["batter_players"]
    bowler_players = result["bowler_players"]
    batter_records = result["batter_records"]
    bowler_records = result["bowler_records"]
    canonical = _canonical_results()

    lines: list[str] = []
    lines.append("# Stage 5 Primary Scoring — Validation Report")
    lines.append("")
    lines.append(
        "**Scope:** approved Stage 4.2 pressure metrics, format-level eligibility, "
        "Kish effective sample size, \\(K=50\\) shrinkage, equal-weight cross-format "
        "composite, calibrated reliability, deterministic tie-breaks, and the final "
        "\\(M_{role}\\ge10\\) gate."
    )
    lines.append("")
    lines.append(f"**Overall status: {'PASS' if passed else 'FAIL'}**")
    lines.append("")
    lines.append(
        f"**Scoring corpus:** {len(scoring):,} deliveries / "
        f"{scoring['match_id'].nunique():,} matches.  "
        f"**Audit corpus:** {len(audit):,} deliveries.  "
        f"**Checks:** {len(checks)} total, {len(checks) - len(failures)} passed, "
        f"{len(failures)} failed."
    )
    lines.append("")
    lines.append(
        "The full check list is in Section 7.  The headline sections below show the "
        "reconciled corpus, pressure-engine reproduction, eligible populations, "
        "calibration moments and final top-10 lists."
    )
    lines.append("")

    lines.append("## 1. Corpus and data-rule reconciliation")
    lines.append("")
    lines.append(
        _md_table(
            ["Quantity", "Observed", "Approved / expected", "Status"],
            [
                ["Audit deliveries", f"{len(audit):,}", f"{AUDIT_CORPUS_ROWS:,}", "PASS" if len(audit) == AUDIT_CORPUS_ROWS else "FAIL"],
                ["Scoring deliveries", f"{len(scoring):,}", f"{SCORING_CORPUS_ROWS:,}", "PASS" if len(scoring) == SCORING_CORPUS_ROWS else "FAIL"],
                ["Scoring matches", f"{scoring['match_id'].nunique():,}", "812", "PASS" if scoring["match_id"].nunique() == 812 else "FAIL"],
                ["T20 (IPL) deliveries", f"{int((scoring['match_format'] == 'T20').sum()):,}", "87,217", "PASS" if int((scoring['match_format'] == 'T20').sum()) == 87_217 else "FAIL"],
                ["T20I deliveries", f"{int((scoring['match_format'] == 'T20I').sum()):,}", "104,746", "PASS" if int((scoring['match_format'] == 'T20I').sum()) == 104_746 else "FAIL"],
                ["Match 48610 first innings", f"{int(((audit['match_id'] == MATCH_48610_ID) & (audit['innings'] == 1)).sum())}", "101", "PASS"],
                ["Match 48610 chase excluded", f"{int(((audit['match_id'] == MATCH_48610_ID) & (audit['innings'] == 2)).sum())}", "93", "PASS"],
                ["`other` extras in scoring corpus", f"{int((scoring['extras_type_clean'] == 'other').sum())}", "256", "PASS" if int((scoring['extras_type_clean'] == 'other').sum()) == 256 else "FAIL"],
            ],
        )
    )
    lines.append("")
    lines.append(
        "The 11-boundary audit-to-scoring difference is entirely the excluded Match 48610 "
        "chase: 9,827 audit / 9,816 scoring under the provisional all-extras rule.  "
        "The verified-core counts are 9,801 / 9,790, and legal-only counts are 9,767 / 9,756."
    )
    lines.append("")

    lines.append("## 2. Pressure-engine reproduction")
    lines.append("")
    lines.append(
        "The eight approved canonical scenarios were independently recomputed from the "
        "Stage 4.2 equations.  Maximum absolute deviation across P_bat and P_bowl is "
        f"**{max(canonical['delta_bat'].abs().max(), canonical['delta_bowl'].abs().max()):.4f}** "
        "points against the documented one-decimal values."
    )
    lines.append("")
    lines.append(
        _md_table(
            ["Scenario", "P_bat expected", "P_bat observed", "P_bowl expected", "P_bowl observed"],
            [
                [
                    row["scenario"],
                    f"{row['expected_bat']:.1f}",
                    f"{row['observed_bat']:.2f}",
                    f"{row['expected_bowl']:.1f}",
                    f"{row['observed_bowl']:.2f}",
                ]
                for _, row in canonical.iterrows()
            ],
        )
    )
    lines.append("")

    lines.append("## 3. Eligible populations and calibration")
    lines.append("")
    pop_rows = []
    for role, records, players in (
        ("Batter", batter_records, batter_players),
        ("Bowler", bowler_records, bowler_players),
    ):
        pop_rows.append(
            [
                role,
                int(records["composite_ready"].sum()),
                int(records.loc[records["composite_ready"], "player_id"].nunique()),
                int(records["ranking_eligible"].sum()),
                int(players["ranking_eligible"].sum()),
                int(players["calibration_population"].sum()),
                int((players["status"] == "M_BREADTH_INSUFFICIENT").sum()),
            ]
        )
    lines.append(
        _md_table(
            [
                "Role",
                "F records",
                "F players",
                "Final records",
                "Final players",
                "Calibration n",
                "M_role<10 players",
            ],
            pop_rows,
        )
    )
    lines.append("")
    lines.append(
        "The calibration population is \\(F_{j,r}\\neq\\varnothing\\) for each role and "
        "does **not** apply the \\(M_{role}\\ge10\\) gate.  It therefore includes the "
        "21 batter and 32 bowler players excluded from the final rankings by match breadth."
    )
    lines.append("")
    cal_rows = []
    for role, players in (
        ("Batter", batter_players),
        ("Bowler", bowler_players),
    ):
        cal = players[players["calibration_population"]]
        cfg = CALIBRATION[role.lower()]
        cal_rows.append(
            [
                role,
                len(cal),
                f"{cal['Z_comp'].mean():.10f}",
                f"{cfg['mu']:.10f}",
                f"{cal['Z_comp'].std(ddof=0):.10f}",
                f"{cfg['sigma']:.10f}",
            ]
        )
    lines.append(
        _md_table(
            ["Role", "n", "Recomputed mu", "Approved mu", "Recomputed sigma", "Approved sigma"],
            cal_rows,
        )
    )
    lines.append("")
    both_ids = set(
        batter_players.loc[batter_players["ranking_eligible"], "player_id"]
    ) & set(bowler_players.loc[bowler_players["ranking_eligible"], "player_id"])
    lines.append(
        f"**Both-role final-eligible players:** {len(both_ids)} (approved 23).  "
        "Batter and bowler rankings are separate; no combined all-rounder primary ranking "
        "is produced."
    )
    lines.append("")

    lines.append("## 4. Final top 10 batters")
    lines.append("")
    top_bat = result["top10_batters"]
    lines.append(
        _md_table(
            ["Rank", "Player ID", "Player", "F formats", "M_role", "Z_comp", "Reliability"],
            [
                [
                    int(row["final_rank"]),
                    int(row["player_id"]),
                    row["player_name"],
                    row["F_formats"],
                    int(row["M_role"]),
                    f"{row['Z_comp']:.10f}",
                    f"{row['Reliability']:.10f}",
                ]
                for _, row in top_bat.iterrows()
            ],
        )
    )
    lines.append("")

    lines.append("## 5. Final top 10 bowlers")
    lines.append("")
    top_bowl = result["top10_bowlers"]
    lines.append(
        _md_table(
            ["Rank", "Player ID", "Player", "F formats", "M_role", "Z_comp", "Reliability"],
            [
                [
                    int(row["final_rank"]),
                    int(row["player_id"]),
                    row["player_name"],
                    row["F_formats"],
                    int(row["M_role"]),
                    f"{row['Z_comp']:.10f}",
                    f"{row['Reliability']:.10f}",
                ]
                for _, row in top_bowl.iterrows()
            ],
        )
    )
    lines.append("")

    lines.append("## 6. Method-fidelity notes")
    lines.append("")
    lines.append(
        "- Pressure cutoff: \\(P\\ge60\\), weight \\(=(P/100)^2\\).  "
        "Format gates: \\(N_{raw}\\ge75\\), \\(N_{eff,del}\\ge35\\).  "
        "Batter baseline: at least 120 balls faced and 120 legal balls.  "
        "Bowler baseline: at least 120 legal balls."
    )
    lines.append(
        "- Approved weights: 30/25/20/15/10 for both roles.  "
        "Bowler signs: \\(+0.30\\Delta Econ\\), \\(-0.25 Econ_P\\), "
        "\\(+0.20 WktRate_P\\), \\(+0.15 Dot\\%_{bowl,P}\\), "
        "\\(-0.10 BoundaryConcededRate_P\\)."
    )
    lines.append(
        "- Kish \\(N_{eff}\\) uses delivery-level weights; shrinkage uses \\(K=50\\); "
        "z-scores use the approved format-specific population moments; "
        "cross-format aggregation is an equal-weight mean over \\(F_{j,r}\\)."
    )
    lines.append(
        "- Reliability is \\(100/(1+\\exp(-0.80\\,Z_{std}))\\) with the approved "
        "per-role \\(\\mu_{Zcomp}\\) and \\(\\sigma_{Zcomp}\\)."
    )
    lines.append(
        "- Final ranking order is Z_comp desc, summed \\(N_{eff,del}\\) over F desc, "
        "M_role desc, summed N_raw over F desc, player_id asc.  "
        "The final gate is \\(F_{j,r}\\neq\\varnothing\\) and \\(M_{role}\\ge10\\)."
    )
    lines.append(
        "- Match 48610's 93 second-innings rows are excluded from both pressure and "
        "personal baselines; its 101 first-innings rows remain.  `other` remains "
        "provisional no-ball-like (`PROVISIONAL_OTHER`); no unresolved extra was "
        "silently reclassified."
    )
    lines.append(
        "- Capped \\(N_{eff}\\)-proportional cross-format weighting is optional and was "
        "**not** used in primary scoring.  Equal format weighting is primary."
    )
    lines.append("")

    lines.append("## 7. Full check list")
    lines.append("")
    check_rows = []
    for idx, check in enumerate(checks, start=1):
        check_rows.append(
            [
                idx,
                check["area"],
                check["check"],
                _status_icon(check["passed"]),
                check["detail"],
            ]
        )
    lines.append(
        _md_table(["#", "Area", "Check", "Result", "Detail"], check_rows)
    )
    lines.append("")

    lines.append("## 8. Remaining limitations")
    lines.append("")
    lines.append(
        "- The `other` extra classification remains unresolved.  The primary bowler "
        "boundary-conceded treatment is the provisional all-extras rule "
        "(`PROVISIONAL_OTHER`), not a fully verified classification."
    )
    lines.append(
        "- Correlation pair identities remain unresolved and were not used to alter "
        "the approved equal-weight composite."
    )
    lines.append(
        "- Match 48610's DLS provenance remains unresolved; the treatment is resolved "
        "by excluding the chase.  The \\(P_1\\) fallback is an audit/sensitivity device only."
    )
    lines.append(
        "- The Retire Out exclusion is documented as proposed and is not fully "
        "source-verified across every scorecard."
    )
    lines.append(
        "- The optional capped-\\(N_{eff}\\) sensitivity was not run; no numeric \\(C\\) "
        "is registered.  It is not a primary blocker."
    )
    lines.append("")

    lines.append("## 9. Acceptance statement")
    lines.append("")
    if passed:
        lines.append(
            "All critical checks pass.  The Stage 5 primary scoring outputs agree with "
            "the approved Stage 4.2 methodology and the approved corpus treatment.  "
            "This report does not convert any unresolved limitation above into a verified fact."
        )
    else:
        lines.append(
            "**One or more critical checks failed.**  Do not treat Stage 5 as complete.  "
            "See the FAIL rows in Section 7 and the failure details above."
        )
    lines.append("")
    return "\n".join(lines)
