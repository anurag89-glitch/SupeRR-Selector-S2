"""Approved-output loading and shared table logic for the SupeRR dashboard.

This module only reads the Stage 5 and Stage 6 CSV outputs.  It never writes
them and never recalculates a score, rank or eligibility decision.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from components import fmt_formats, fmt_int

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGE5_DIR = PROJECT_ROOT / "outputs" / "stage5"
STAGE6_DIR = PROJECT_ROOT / "outputs" / "stage6"

ROLE_LABELS = {"batter": "Batter", "bowler": "Bowler"}

DATA_FILES = {
    "batter_scoring": STAGE5_DIR / "batter_scoring.csv",
    "bowler_scoring": STAGE5_DIR / "bowler_scoring.csv",
    "batter_format": STAGE5_DIR / "batter_format_records.csv",
    "bowler_format": STAGE5_DIR / "bowler_format_records.csv",
    "top10_batters": STAGE5_DIR / "top10_batters.csv",
    "top10_bowlers": STAGE5_DIR / "top10_bowlers.csv",
    "player_rank_changes": STAGE6_DIR / "player_rank_changes.csv",
    "batter_sensitivity": STAGE6_DIR / "batter_sensitivity_rankings.csv",
    "bowler_sensitivity": STAGE6_DIR / "bowler_sensitivity_rankings.csv",
    "sensitivity_summary": STAGE6_DIR / "sensitivity_summary.csv",
    "batter_stability": STAGE6_DIR / "batter_top10_stability.csv",
    "bowler_stability": STAGE6_DIR / "bowler_top10_stability.csv",
    "eligibility_sensitivity": STAGE6_DIR / "eligibility_sensitivity.csv",
    "scenario_diagnostics": STAGE6_DIR / "scenario_diagnostics.csv",
    "validation_checks": STAGE6_DIR / "stage6_validation_checks.csv",
}


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, pd.DataFrame]:
    """Load approved Stage 5 and Stage 6 CSV outputs exactly as generated."""
    missing = [str(path) for path in DATA_FILES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required approved outputs:\n" + "\n".join(missing)
        )
    return {name: pd.read_csv(path) for name, path in DATA_FILES.items()}


def _bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(bool)


def prepare_data(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Normalize display dtypes without changing any approved value."""
    data: dict[str, pd.DataFrame] = {}

    for role in ("batter", "bowler"):
        scoring = raw[f"{role}_scoring"].copy()
        scoring["ranking_eligible"] = _bool(scoring["ranking_eligible"])
        scoring["F_nonempty"] = _bool(scoring["F_nonempty"])
        scoring["calibration_population"] = _bool(scoring["calibration_population"])
        scoring["F_formats"] = scoring["F_formats"].fillna("—")
        scoring["player_name"] = scoring["player_name"].fillna("Unknown player")
        scoring["role_key"] = role
        data[f"{role}_scoring"] = scoring

        records = raw[f"{role}_format"].copy()
        for column in (
            "baseline_ok",
            "format_gate",
            "composite_ready",
            "ranking_eligible",
            "F_nonempty",
        ):
            if column in records.columns:
                records[column] = _bool(records[column])
        records["format_label"] = records["format_label"].fillna("—")
        records["player_name"] = records["player_name"].fillna("Unknown player")
        data[f"{role}_format"] = records

    data["top10_batter"] = raw["top10_batters"].copy()
    data["top10_bowler"] = raw["top10_bowlers"].copy()
    for role in ("batter", "bowler"):
        sensitivity = raw[f"{role}_sensitivity"].copy()
        for column in (
            "ranking_eligible",
            "in_primary_top10",
            "in_scenario_top10",
            "primary_eligible",
            "scenario_eligible",
        ):
            if column in sensitivity.columns:
                sensitivity[column] = _bool(sensitivity[column])
        sensitivity["player_name"] = sensitivity["player_name"].fillna("Unknown player")
        data[f"{role}_sensitivity"] = sensitivity
    data["player_rank_changes"] = raw["player_rank_changes"].copy()
    data["sensitivity_summary"] = raw["sensitivity_summary"].copy()
    data["batter_stability"] = raw["batter_stability"].copy()
    data["bowler_stability"] = raw["bowler_stability"].copy()
    data["eligibility_sensitivity"] = raw["eligibility_sensitivity"].copy()
    data["scenario_diagnostics"] = raw["scenario_diagnostics"].copy()
    data["validation_checks"] = raw["validation_checks"].copy()

    for role in ("batter", "bowler"):
        rank = data[f"{role}_scoring"].copy()
        rank["role_label"] = ROLE_LABELS[role]
        data[f"{role}_players"] = rank

    combined = pd.concat(
        [data["batter_players"], data["bowler_players"]], ignore_index=True
    )
    data["all_player_rows"] = combined

    player_index = (
        combined.groupby(["player_id", "player_name"], dropna=False)
        .agg(
            roles=("role_key", lambda values: tuple(sorted(set(values)))),
            best_rank=("final_rank", "min"),
            role_count=("role_key", "nunique"),
        )
        .reset_index()
    )
    player_index["player_name"] = player_index["player_name"].fillna("Unknown player")
    player_index["search"] = (
        player_index["player_name"].astype(str)
        + " "
        + player_index["player_id"].astype(str)
    ).str.lower()
    data["player_index"] = player_index
    return data


def top10_display(top10: pd.DataFrame) -> pd.DataFrame:
    display = top10.rename(
        columns={
            "final_rank": "Rank",
            "player_name": "Player",
            "player_id": "Player ID",
            "F_formats": "Eligible formats",
            "M_role": "Matches",
            "sum_N_raw_F": "N_raw",
            "sum_N_eff_del_F": "N_eff",
            "Z_comp": "Composite Z",
            "Reliability": "Reliability",
        }
    )
    display["Eligible formats"] = display["Eligible formats"].map(fmt_formats)
    return display[
        [
            "Rank",
            "Player",
            "Player ID",
            "Eligible formats",
            "Matches",
            "N_raw",
            "N_eff",
            "Composite Z",
            "Reliability",
        ]
    ]


def top10_column_config() -> dict[str, st.column_config.Column]:
    return {
        "Rank": st.column_config.NumberColumn(
            format="%d",
            width="small",
            help="Approved Stage 5 final rank.",
        ),
        "Player": st.column_config.TextColumn(width="medium"),
        "Player ID": st.column_config.NumberColumn(format="%d", width="small"),
        "Eligible formats": st.column_config.TextColumn(
            width="medium",
            help="Formats in the approved set F for this player-role.",
        ),
        "Matches": st.column_config.NumberColumn(
            format="%d",
            width="small",
            help="M_role: eligible matches across the qualifying formats.",
        ),
        "N_raw": st.column_config.NumberColumn(
            format="%d",
            help="Pressure deliveries before the Kish effective-sample adjustment.",
        ),
        "N_eff": st.column_config.NumberColumn(
            format="%.1f",
            help="Effective pressure deliveries after the Kish adjustment.",
        ),
        "Composite Z": st.column_config.NumberColumn(
            format="%.4f",
            help="Approved pressure-adjusted composite score.",
        ),
        "Reliability": st.column_config.NumberColumn(
            format="%.2f",
            help="Calibrated 0-100 precision index, not a probability.",
        ),
    }


def _clear_top10_filters(role: str) -> None:
    """Reset display filters before the widgets are re-instantiated."""
    st.session_state[f"top10_query_{role}"] = ""
    st.session_state[f"top10_format_{role}"] = "All formats"
    st.session_state[f"top10_sort_{role}"] = "Final rank"


def top10_view(
    top10: pd.DataFrame, query: str, format_filter: str, sort_label: str
) -> pd.DataFrame:
    view = top10.copy()
    if query.strip():
        needle = query.strip().lower()
        mask = (
            view["player_name"].astype(str).str.lower().str.contains(needle, regex=False)
            | view["player_id"].astype(str).str.contains(needle, regex=False)
        )
        view = view[mask]
    if format_filter != "All formats":
        view = view[
            view["F_formats"].astype(str).str.contains(format_filter, regex=False)
        ]
    sort_map = {
        "Final rank": ("final_rank", True),
        "Reliability (high to low)": ("Reliability", False),
        "Composite score (high to low)": ("Z_comp", False),
        "Match count (high to low)": ("M_role", False),
        "Player name (A-Z)": ("player_name", True),
    }
    sort_column, ascending = sort_map[sort_label]
    return view.sort_values(sort_column, ascending=ascending, kind="mergesort")


def _comparison_table(
    data: dict[str, pd.DataFrame], role: str, scenario_id: str
) -> pd.DataFrame:
    rankings = data[f"{role}_sensitivity"]
    table = rankings[rankings["scenario_id"] == scenario_id].copy()
    table = table[
        (table["in_primary_top10"] == True) | (table["in_scenario_top10"] == True)
    ].copy()
    if table.empty:
        return table

    def membership(row: pd.Series) -> str:
        if bool(row["in_primary_top10"]) and bool(row["in_scenario_top10"]):
            return "Retained"
        if bool(row["in_scenario_top10"]):
            return "Entrant"
        return "Leaver"

    table["Membership"] = table.apply(membership, axis=1)
    table["Primary rank"] = table["primary_rank"]
    table["Scenario rank"] = table["final_rank"]
    table["Delta rank"] = table["rank_change_vs_primary"]
    table = table.sort_values(
        ["final_rank", "primary_rank", "player_id"], na_position="last"
    )
    return table


def _movement_tables(
    data: dict[str, pd.DataFrame], role: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    table = data["player_rank_changes"]
    table = table[(table["role"] == role) & (table["primary_top10"] == True)].copy()
    table = table[pd.to_numeric(table["scenarios_eligible_approved"], errors="coerce") >= 10]
    table = table.sort_values("mean_abs_rank_change_approved")
    stable = table.head(6).copy()
    sensitive = table.sort_values(
        "mean_abs_rank_change_approved", ascending=False
    ).head(6).copy()
    return stable, sensitive


def _movement_display(table: pd.DataFrame) -> pd.DataFrame:
    display = table[
        [
            "player_name",
            "primary_rank",
            "top10_appearances_approved",
            "scenarios_eligible_approved",
            "mean_abs_rank_change_approved",
            "max_abs_rank_change_approved",
            "max_abs_rank_change_scenario_approved",
            "mean_abs_Z_change_approved",
        ]
    ].copy()
    display["Top-10 appearances"] = [
        f"{fmt_int(appearances)} / {fmt_int(total)}"
        for appearances, total in zip(
            display["top10_appearances_approved"],
            display["scenarios_eligible_approved"],
        )
    ]
    display = display.drop(columns=["top10_appearances_approved", "scenarios_eligible_approved"])
    return display.rename(
        columns={
            "player_name": "Player",
            "primary_rank": "Rank",
            "mean_abs_rank_change_approved": "Mean |Δrank|",
            "max_abs_rank_change_approved": "Max |Δrank|",
            "max_abs_rank_change_scenario_approved": "Worst scenario",
            "mean_abs_Z_change_approved": "Mean |ΔZ|",
        }
    )


__all__ = [
    "DATA_FILES",
    "PROJECT_ROOT",
    "ROLE_LABELS",
    "STAGE5_DIR",
    "STAGE6_DIR",
    "_bool",
    "_clear_top10_filters",
    "_comparison_table",
    "_movement_display",
    "_movement_tables",
    "load_data",
    "prepare_data",
    "top10_column_config",
    "top10_display",
    "top10_view",
]
