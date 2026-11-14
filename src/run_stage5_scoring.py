"""
Stage 5 primary scoring runner.

Usage:
    python src/run_stage5_scoring.py

Reads the approved pressure-feature dataset, builds the batter and bowler
primary scoring tables, writes the Stage 5 outputs, and generates the
validation report.  It never writes to data/raw or data/processed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from stage5_config import OUTPUT_DIR, OUTPUT_FILES, REPORT_DIR
from stage5_scoring import build_stage5_tables
from stage5_validation import build_validation_report, run_validation_checks

BATTER_RECORD_COLUMNS = [
    "role", "player_id", "player_name", "match_format", "format_label",
    "N_raw", "N_eff_del", "M_format",
    "baseline_BF", "baseline_legal", "base_deliveries", "base_matches",
    "baseline_ok", "SR_base", "Dot_base", "DR_base",
    "SR_P", "Boundary_P", "Dot_P", "DR_P", "dSR", "dDot", "dDR",
    "N_eff_BF", "N_eff_legal",
    "den_dSR", "den_SR_P", "den_Boundary_P", "den_dDot", "den_dDR",
    "denoms_ok",
    "shrunk_dSR", "z_dSR", "shrunk_SR_P", "z_SR_P",
    "shrunk_Boundary_P", "z_Boundary_P", "shrunk_dDot", "z_dDot",
    "shrunk_dDR", "z_dDR", "Z_comp_format",
    "format_gate", "finite_Z", "composite_ready", "F_nonempty",
    "M_role", "M_all", "ranking_eligible", "record_status",
    "exclusion_detail",
]

BOWLER_RECORD_COLUMNS = [
    "role", "player_id", "player_name", "match_format", "format_label",
    "N_raw", "N_eff_del", "M_format",
    "baseline_legal", "base_deliveries", "base_matches", "baseline_ok",
    "Econ_base", "Dot_base", "BoundaryConc_base",
    "Econ_P", "WktRate_P", "Dot_bowl_P", "BoundaryConc_P", "dEcon",
    "N_eff_legal",
    "den_dEcon", "den_Econ_P", "den_WktRate_P", "den_Dot_bowl_P",
    "den_BoundaryConc_P", "denoms_ok",
    "shrunk_dEcon", "z_dEcon", "shrunk_Econ_P", "z_Econ_P",
    "shrunk_WktRate_P", "z_WktRate_P", "shrunk_Dot_bowl_P",
    "z_Dot_bowl_P", "shrunk_BoundaryConc_P", "z_BoundaryConc_P",
    "Z_comp_format",
    "format_gate", "finite_Z", "composite_ready", "F_nonempty",
    "M_role", "M_all", "ranking_eligible", "record_status",
    "exclusion_detail",
]

PLAYER_COLUMNS = [
    "role", "player_id", "player_name", "F_formats", "n_formats_F",
    "F_nonempty", "M_role", "M_all", "sum_N_raw_F", "sum_N_eff_del_F",
    "Z_comp", "Z_std", "Reliability", "ranking_eligible", "final_rank",
    "status", "exclusion_detail", "calibration_population",
]

TOP10_COLUMNS = [
    "final_rank", "role", "player_id", "player_name", "F_formats",
    "M_role", "sum_N_raw_F", "sum_N_eff_del_F",
    "Z_comp", "Z_std", "Reliability",
]

FORMAT_AUDIT_COLUMNS = [
    "role", "player_id", "player_name", "match_format",
    "N_raw", "N_eff_del", "M_format", "baseline_ok", "denoms_ok",
    "format_gate", "finite_Z", "composite_ready", "F_nonempty",
    "M_role", "M_all", "ranking_eligible", "record_status",
    "exclusion_detail",
]


def _write_csv(df: pd.DataFrame, filename: str, columns: list[str]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    out = df.reindex(columns=columns).copy()
    out.to_csv(path, index=False, float_format="%.10f", na_rep="")
    return path


def write_stage5_outputs(result: dict) -> list[Path]:
    """Write all Stage 5 CSV outputs and return their paths."""
    paths = []
    paths.append(
        _write_csv(
            result["batter_records"],
            OUTPUT_FILES["batter_format_records"],
            BATTER_RECORD_COLUMNS,
        )
    )
    paths.append(
        _write_csv(
            result["bowler_records"],
            OUTPUT_FILES["bowler_format_records"],
            BOWLER_RECORD_COLUMNS,
        )
    )
    paths.append(
        _write_csv(
            result["batter_players"], OUTPUT_FILES["batter_scoring"], PLAYER_COLUMNS
        )
    )
    paths.append(
        _write_csv(
            result["bowler_players"], OUTPUT_FILES["bowler_scoring"], PLAYER_COLUMNS
        )
    )
    paths.append(
        _write_csv(
            result["top10_batters"], OUTPUT_FILES["top10_batters"], TOP10_COLUMNS
        )
    )
    paths.append(
        _write_csv(
            result["top10_bowlers"], OUTPUT_FILES["top10_bowlers"], TOP10_COLUMNS
        )
    )

    # Player-level eligibility audit: one row per player-role, all evaluated
    # players, including those excluded before the final ranking gate.
    audit = pd.concat(
        [result["batter_players"], result["bowler_players"]], ignore_index=True
    )
    audit["eligibility_status"] = audit["status"]
    audit["in_primary_ranking"] = audit["ranking_eligible"]
    paths.append(
        _write_csv(
            audit,
            OUTPUT_FILES["eligibility_audit"],
            PLAYER_COLUMNS + ["eligibility_status", "in_primary_ranking"],
        )
    )

    # Format-level audit: one row per player-format record.
    fmt_audit = pd.concat(
        [result["batter_records"], result["bowler_records"]], ignore_index=True
    )
    paths.append(
        _write_csv(
            fmt_audit,
            OUTPUT_FILES["format_eligibility_audit"],
            FORMAT_AUDIT_COLUMNS,
        )
    )

    cal = audit[audit["calibration_population"]].copy()
    paths.append(
        _write_csv(
            cal,
            OUTPUT_FILES["calibration_population"],
            PLAYER_COLUMNS,
        )
    )
    return paths


def _print_top(label: str, df: pd.DataFrame) -> None:
    print(f"\n{label}")
    cols = ["final_rank", "player_id", "player_name", "Reliability", "Z_comp", "M_role"]
    print(df[cols].to_string(index=False))


def main() -> int:
    print("Stage 5 — primary scoring implementation")
    print("Loading approved 192,056-row audit corpus...")
    result = build_stage5_tables()

    print(
        f"Scoring corpus: {len(result['scoring']):,} deliveries / "
        f"{result['scoring']['match_id'].nunique():,} matches"
    )
    paths = write_stage5_outputs(result)
    print(f"Wrote {len(paths)} CSV outputs to {OUTPUT_DIR}")

    checks = run_validation_checks(result, check_outputs=True)
    report = build_validation_report(result, checks=checks)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / OUTPUT_FILES["scoring_validation"]
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote validation report to {report_path}")

    failed = [check for check in checks if not check["passed"]]
    print(
        f"Validation: {len(checks) - len(failed)}/{len(checks)} checks passed"
    )
    if failed:
        print("VALIDATION FAILED:")
        for check in failed:
            print(f"  [{check['area']}] {check['check']}: {check['detail']}")

    for role in ("batter", "bowler"):
        players = result[f"{role}_players"]
        print(
            f"{role}: {int(players['calibration_population'].sum())} calibration, "
            f"{int(players['ranking_eligible'].sum())} final eligible, "
            f"{int((players['status'] == 'M_BREADTH_INSUFFICIENT').sum())} M<10"
        )
    both = set(
        result["batter_players"].loc[
            result["batter_players"]["ranking_eligible"], "player_id"
        ]
    ) & set(
        result["bowler_players"].loc[
            result["bowler_players"]["ranking_eligible"], "player_id"
        ]
    )
    print(f"Both roles final eligible: {len(both)}")

    _print_top("Top 10 batters", result["top10_batters"])
    _print_top("Top 10 bowlers", result["top10_bowlers"])
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
