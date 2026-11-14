"""
Stage 6 sensitivity runner.

Runs every registered executable sensitivity, writes the seven required Stage 6
CSV outputs, builds the Markdown report and runs the independent validation
layer.  Stage 5 primary outputs and all input datasets are read-only.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stage5_config import OUTPUT_DIR as STAGE5_OUTPUT_DIR  # noqa: E402
from stage6_config import (  # noqa: E402
    COMPLETED_SCENARIOS,
    OUTPUT_DIR,
    OUTPUT_FILES,
    REPORT_PATH,
    SCENARIOS,
    SCENARIO_BY_ID,
    SCORING_DATA_PATH,
)
from stage6_scoring import (  # noqa: E402
    align_scenario_players,
    compare_top10,
    correlate_common,
    load_stage6_corpus,
    run_scenario,
    top_n,
)
from stage6_report import build_sensitivity_report  # noqa: E402
from stage6_validation import run_report_checks, run_stage6_checks  # noqa: E402

RAW_FILES = [
    PROJECT_ROOT / "data" / "raw" / "ball_by_ball.csv",
    PROJECT_ROOT / "data" / "raw" / "matches.csv",
    PROJECT_ROOT / "data" / "raw" / "playing_eleven.csv",
    PROJECT_ROOT / "data" / "raw" / "competitions.csv",
    PROJECT_ROOT / "data" / "raw" / "teams.csv",
    PROJECT_ROOT / "data" / "raw" / "competition_team_player_mapping.csv",
]
PROCESSED_FILES = [
    SCORING_DATA_PATH,
    PROJECT_ROOT / "data" / "processed" / "cleaned_deliveries.csv",
    PROJECT_ROOT / "data" / "processed" / "interrupted_delivery_features.csv",
    PROJECT_ROOT / "data" / "processed" / "super_over_delivery_features.csv",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_inputs() -> dict:
    out = {}
    for path in RAW_FILES + PROCESSED_FILES + sorted(STAGE5_OUTPUT_DIR.glob("*.csv")):
        out[str(path.relative_to(PROJECT_ROOT))] = sha256(path)
    return out


def _ids_text(values) -> str:
    clean = [str(int(v)) for v in values if pd.notna(v)]
    return ";".join(clean)


def _scenario_summary_row(
    result: dict,
    primary: dict,
    role_metrics: dict,
) -> dict:
    scenario = result["scenario"]
    diag = result["diagnostics"]
    row = {
        "scenario_id": scenario.scenario_id,
        "category": scenario.category,
        "status": scenario.status,
        "approved": scenario.approved,
        "mandatory": scenario.mandatory,
        "description": scenario.description,
        "change_from_primary": scenario.change_from_primary,
        "parameters": scenario.parameter_text(),
        "blocked_reason": scenario.blocked_reason,
        "corpus_rows": diag["corpus_rows"],
        "matches": diag["matches"],
        "seasons": diag["seasons"],
        "pressure_batter_rows": diag["pressure_batter_rows"],
        "pressure_bowler_rows": diag["pressure_bowler_rows"],
        "boundary_count_all": diag["boundary_count_all"],
        "boundary_count_legal_overstep": diag["boundary_count_legal_overstep"],
        "boundary_count_legal_only": diag["boundary_count_legal_only"],
        "other_rows": diag["other_rows"],
        "other_legal_rows": diag["other_legal_rows"],
        "other_pressure_bowler_rows": diag["other_pressure_bowler_rows"],
        "widestump_pressure_rows": diag["widestump_pressure_rows"],
        "wide_dismissal_pressure_rows": diag["wide_dismissal_pressure_rows"],
        "p_bat_mean": diag["p_bat_mean"],
        "p_bowl_mean": diag["p_bowl_mean"],
    }
    for role in ("batter", "bowler"):
        m = role_metrics[role]
        row.update(
            {
                f"{role}_primary_eligible_count": int(
                    primary[f"{role}_players"]["ranking_eligible"].sum()
                ),
                f"{role}_eligible_count": int(
                    result[f"{role}_players"]["ranking_eligible"].sum()
                ),
                f"{role}_common_n": m["common_n"],
                f"{role}_top10_overlap": m["top10_overlap"],
                f"{role}_top10_jaccard": m["top10_jaccard"],
                f"{role}_spearman": m["spearman_rank"],
                f"{role}_kendall": m["kendall_rank"],
                f"{role}_spearman_z": m["spearman_z"],
                f"{role}_kendall_z": m["kendall_z"],
                f"{role}_entrants": len(m["entrants"]),
                f"{role}_leavers": len(m["leavers"]),
                f"{role}_mean_abs_rank_change": m["mean_abs_rank_change"],
                f"{role}_max_abs_rank_change": m["max_abs_rank_change"],
            }
        )
    return row


def _blocked_summary_row(scenario) -> dict:
    return {
        "scenario_id": scenario.scenario_id,
        "category": scenario.category,
        "status": scenario.status,
        "approved": scenario.approved,
        "mandatory": scenario.mandatory,
        "description": scenario.description,
        "change_from_primary": scenario.change_from_primary,
        "parameters": scenario.parameter_text(),
        "blocked_reason": scenario.blocked_reason,
    }


def _top10_row(
    result: dict, primary: dict, role: str, metrics: dict
) -> dict:
    scenario = result["scenario"]
    p_ids = metrics["primary_top10"]
    s_ids = metrics["scenario_top10"]
    return {
        "scenario_id": scenario.scenario_id,
        "role": role,
        "category": scenario.category,
        "status": scenario.status,
        "approved": scenario.approved,
        "eligible_count": int(result[f"{role}_players"]["ranking_eligible"].sum()),
        "primary_eligible_count": int(
            primary[f"{role}_players"]["ranking_eligible"].sum()
        ),
        "top10_overlap": metrics["top10_overlap"],
        "top10_jaccard": metrics["top10_jaccard"],
        "retained_count": len(metrics["retained"]),
        "entrant_count": len(metrics["entrants"]),
        "leaver_count": len(metrics["leavers"]),
        "spearman_rank": metrics["spearman_rank"],
        "kendall_rank": metrics["kendall_rank"],
        "spearman_z": metrics["spearman_z"],
        "kendall_z": metrics["kendall_z"],
        "common_n": metrics["common_n"],
        "mean_abs_rank_change": metrics["mean_abs_rank_change"],
        "max_abs_rank_change": metrics["max_abs_rank_change"],
        "top10_changed": bool(metrics["top10_overlap"] < 10),
        "primary_top10_ids": _ids_text(p_ids),
        "scenario_top10_ids": _ids_text(s_ids),
        "retained_ids": _ids_text(metrics["retained"]),
        "entrant_ids": _ids_text(metrics["entrants"]),
        "leaver_ids": _ids_text(metrics["leavers"]),
    }


def _eligibility_row(
    result: dict, primary: dict, role: str, aligned: pd.DataFrame
) -> dict:
    scenario = result["scenario"]
    p_ids = set(
        primary[f"{role}_players"].loc[
            primary[f"{role}_players"]["ranking_eligible"], "player_id"
        ]
    )
    s_ids = set(
        result[f"{role}_players"].loc[
            result[f"{role}_players"]["ranking_eligible"], "player_id"
        ]
    )
    newly = sorted(s_ids - p_ids)
    lost = sorted(p_ids - s_ids)
    return {
        "scenario_id": scenario.scenario_id,
        "role": role,
        "category": scenario.category,
        "status": scenario.status,
        "approved": scenario.approved,
        "primary_eligible_count": len(p_ids),
        "scenario_eligible_count": len(s_ids),
        "delta_eligible": len(s_ids) - len(p_ids),
        "common_eligible_count": len(p_ids & s_ids),
        "newly_eligible_count": len(newly),
        "no_longer_eligible_count": len(lost),
        "primary_universe_count": int(len(primary[f"{role}_players"])),
        "scenario_universe_count": int(len(result[f"{role}_players"])),
        "newly_eligible_ids": _ids_text(newly),
        "no_longer_eligible_ids": _ids_text(lost),
        "eligibility_rule": (
            "F non-empty AND M_all>=10"
            if scenario.eligibility == "m_all"
            else (
                "F non-empty with M_format>=10 per format AND M_role>=10"
                if scenario.eligibility == "per_format_m10"
                else "F non-empty AND M_role>=10"
            )
        ),
    }


def _ranking_rows(
    scenario_id: str,
    scenario_status: str,
    role: str,
    aligned: pd.DataFrame,
) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "scenario_id": scenario_id,
            "scenario_status": scenario_status,
            "role": role,
            "player_id": aligned["player_id"].astype(int),
            "player_name": aligned["player_name"],
            "ranking_eligible": aligned["scenario_eligible"].astype(bool),
            "final_rank": aligned["scenario_rank"],
            "Z_comp": aligned["scenario_Z_comp"],
            "Z_std": aligned["scenario_Z_std"],
            "Reliability": aligned["scenario_Reliability"],
            "M_role": aligned["scenario_M_role"],
            "M_all": aligned["scenario_M_all"],
            "sum_N_raw_F": aligned["scenario_sum_N_raw_F"],
            "sum_N_eff_del_F": aligned["scenario_sum_N_eff_del_F"],
            "F_formats": aligned["scenario_F_formats"],
            "status": aligned["scenario_status"],
            "primary_rank": aligned["primary_rank"],
            "primary_Z_comp": aligned["primary_Z_comp"],
            "primary_Reliability": aligned["primary_Reliability"],
            "rank_change_vs_primary": aligned["rank_change_vs_primary"],
            "Z_change_vs_primary": aligned["Z_change_vs_primary"],
            "Reliability_change_vs_primary": aligned[
                "Reliability_change_vs_primary"
            ],
            "in_primary_top10": aligned["in_primary_top10"].astype(bool),
            "in_scenario_top10": aligned["in_scenario_top10"].astype(bool),
            "primary_eligible": aligned["primary_eligible"].astype(bool),
            "scenario_eligible": aligned["scenario_eligible"].astype(bool),
        }
    )
    return out


def _player_change_rows(
    role: str,
    primary_players: pd.DataFrame,
    aligned_frames: list[pd.DataFrame],
    scenario_ids: list[str],
) -> pd.DataFrame:
    primary = primary_players.set_index("player_id")
    records = {}
    for frame in aligned_frames:
        sid = str(frame["scenario_id"].iloc[0])
        if sid == "PRIMARY":
            continue
        approved = bool(SCENARIO_BY_ID[sid].approved)
        for row in frame.itertuples(index=False):
            rec = records.setdefault(
                int(row.player_id),
                {
                    "player_name": row.player_name,
                    "ranks": [],
                    "z_changes": [],
                    "eligible": 0,
                    "top10": 0,
                    "eligible_approved": 0,
                    "top10_approved": 0,
                },
            )
            if pd.notna(row.player_name) and (
                rec["player_name"] is None or pd.isna(rec["player_name"])
            ):
                rec["player_name"] = row.player_name
            if bool(row.scenario_eligible):
                rec["eligible"] += 1
                if approved:
                    rec["eligible_approved"] += 1
                if pd.notna(row.scenario_rank):
                    rec["ranks"].append((sid, float(row.scenario_rank), approved))
                if bool(row.in_scenario_top10):
                    rec["top10"] += 1
                    if approved:
                        rec["top10_approved"] += 1
            if (
                bool(row.primary_eligible)
                and bool(row.scenario_eligible)
                and pd.notna(row.primary_rank)
                and pd.notna(row.scenario_rank)
                and pd.notna(row.Z_change_vs_primary)
            ):
                rec["z_changes"].append(
                    (sid, float(row.Z_change_vs_primary), approved)
                )

    rows = []
    for player_id, rec in records.items():
        if player_id not in primary.index:
            primary_rank = np.nan
            primary_z = np.nan
            primary_rel = np.nan
            primary_status = "NOT_IN_PRIMARY"
        else:
            prow = primary.loc[player_id]
            primary_rank = prow["final_rank"] if prow["ranking_eligible"] else np.nan
            primary_z = prow["Z_comp"]
            primary_rel = prow["Reliability"]
            primary_status = prow["status"]

        rank_changes = []
        rank_changes_approved = []
        for sid, rank, approved in rec["ranks"]:
            if pd.notna(primary_rank):
                change = (sid, rank - float(primary_rank))
                rank_changes.append(change)
                if approved:
                    rank_changes_approved.append(change)
        abs_changes = [(sid, abs(v)) for sid, v in rank_changes]
        abs_changes_approved = [(sid, abs(v)) for sid, v in rank_changes_approved]
        z_abs = [(sid, abs(v)) for sid, v, _ in rec["z_changes"]]
        z_abs_approved = [
            (sid, abs(v)) for sid, v, approved in rec["z_changes"] if approved
        ]

        def _mean(vals):
            return float(np.mean(vals)) if vals else np.nan

        def _max(vals):
            return float(np.max(vals)) if vals else np.nan

        def _argmax(vals):
            return max(vals, key=lambda x: x[1])[0] if vals else ""

        mean_abs = _mean([v for _, v in abs_changes])
        max_abs = _max([v for _, v in abs_changes])
        mean_rank = _mean([v for _, v in rank_changes])
        mean_abs_z = _mean([v for _, v in z_abs])
        max_abs_z = _max([v for _, v in z_abs])
        mean_abs_approved = _mean([v for _, v in abs_changes_approved])
        max_abs_approved = _max([v for _, v in abs_changes_approved])
        mean_abs_z_approved = _mean([v for _, v in z_abs_approved])
        max_abs_z_approved = _max([v for _, v in z_abs_approved])
        scenario_ranks = [v for _, v, _ in rec["ranks"]]

        rows.append(
            {
                "role": role,
                "player_id": player_id,
                "player_name": rec["player_name"],
                "primary_rank": primary_rank,
                "primary_Z_comp": primary_z,
                "primary_Reliability": primary_rel,
                "primary_top10": bool(
                    pd.notna(primary_rank) and float(primary_rank) <= 10
                ),
                "primary_status": primary_status,
                "scenarios_total": len(scenario_ids),
                "scenarios_eligible": rec["eligible"],
                "scenarios_ineligible": len(scenario_ids) - rec["eligible"],
                "scenarios_eligible_approved": rec["eligible_approved"],
                "rank_change_scenarios": len(rank_changes),
                "rank_change_scenarios_approved": len(rank_changes_approved),
                "top10_appearances": rec["top10"],
                "top10_appearances_approved": rec["top10_approved"],
                "mean_abs_rank_change": mean_abs,
                "max_abs_rank_change": max_abs,
                "max_abs_rank_change_scenario": _argmax(abs_changes),
                "mean_abs_rank_change_approved": mean_abs_approved,
                "max_abs_rank_change_approved": max_abs_approved,
                "max_abs_rank_change_scenario_approved": _argmax(abs_changes_approved),
                "mean_rank_change": mean_rank,
                "mean_abs_Z_change": mean_abs_z,
                "max_abs_Z_change": max_abs_z,
                "max_abs_Z_change_scenario": _argmax(z_abs),
                "mean_abs_Z_change_approved": mean_abs_z_approved,
                "max_abs_Z_change_approved": max_abs_z_approved,
                "max_abs_Z_change_scenario_approved": _argmax(z_abs_approved),
                "best_rank": min(scenario_ranks) if scenario_ranks else np.nan,
                "worst_rank": max(scenario_ranks) if scenario_ranks else np.nan,
                "median_rank": float(np.median(scenario_ranks))
                if scenario_ranks
                else np.nan,
                "eligible_in_all_scenarios": rec["eligible"] == len(scenario_ids),
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values(["role", "primary_rank", "player_id"], na_position="last")


def main() -> int:
    start = time.time()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Hashing inputs ...")
    hashes_before = hash_inputs()

    print("Loading Stage 6 corpus ...")
    base = load_stage6_corpus()
    print(f"  audit corpus: {len(base):,} rows / {base.match_id.nunique()} matches")

    print("Running PRIMARY ...")
    primary = run_scenario(base, SCENARIO_BY_ID["PRIMARY"], keep_deliveries=False)

    summary_rows = []
    top10_rows = {"batter": [], "bowler": []}
    eligibility_rows = []
    ranking_frames = {"batter": [], "bowler": []}
    aligned_frames = {"batter": [], "bowler": []}
    diagnostics_rows = []
    scenario_results = {}

    def process_result(result: dict) -> None:
        scenario = result["scenario"]
        role_metrics = {}
        for role in ("batter", "bowler"):
            m = correlate_common(primary[f"{role}_players"], result[f"{role}_players"])
            m.update(compare_top10(primary[f"{role}_players"], result[f"{role}_players"]))
            role_metrics[role] = m
            aligned = align_scenario_players(
                primary[f"{role}_players"],
                result[f"{role}_players"],
                scenario.scenario_id,
                role,
            )
            aligned_frames[role].append(aligned)
            ranking_frames[role].append(
                _ranking_rows(scenario.scenario_id, scenario.status, role, aligned)
            )
            top10_rows[role].append(_top10_row(result, primary, role, m))
            eligibility_rows.append(_eligibility_row(result, primary, role, aligned))
        summary_rows.append(_scenario_summary_row(result, primary, role_metrics))
        diagnostics_rows.append(result["diagnostics"])
        scenario_results[scenario.scenario_id] = result

    process_result(primary)

    completed = [
        s for s in COMPLETED_SCENARIOS if s.scenario_id != "PRIMARY"
    ]
    for i, scenario in enumerate(completed, start=1):
        t0 = time.time()
        print(f"[{i:02d}/{len(completed)}] {scenario.scenario_id} ...", end="", flush=True)
        result = run_scenario(base, scenario, keep_deliveries=False)
        process_result(result)
        print(f" {time.time() - t0:.1f}s")

    print("Building player rank-change summary ...")
    completed_ids = [s.scenario_id for s in completed]
    player_changes = pd.concat(
        [
            _player_change_rows(
                role, primary[f"{role}_players"], aligned_frames[role], completed_ids
            )
            for role in ("batter", "bowler")
        ],
        ignore_index=True,
    )

    print("Writing CSVs ...")
    rankings = {
        role: pd.concat(ranking_frames[role], ignore_index=True)
        for role in ("batter", "bowler")
    }
    for role, frame in rankings.items():
        frame.to_csv(
            OUTPUT_DIR / OUTPUT_FILES[f"{role}_sensitivity_rankings"], index=False
        )

    top10_frames = {
        role: pd.DataFrame(top10_rows[role]) for role in ("batter", "bowler")
    }
    for role, frame in top10_frames.items():
        frame.to_csv(
            OUTPUT_DIR / OUTPUT_FILES[f"{role}_top10_stability"], index=False
        )

    eligibility = pd.DataFrame(eligibility_rows)
    eligibility.to_csv(
        OUTPUT_DIR / OUTPUT_FILES["eligibility_sensitivity"], index=False
    )

    player_changes.to_csv(
        OUTPUT_DIR / OUTPUT_FILES["player_rank_changes"], index=False
    )

    summary = pd.DataFrame(summary_rows)
    # Add blocked / optional rows without fabricated metrics.
    blocked_rows = [
        _blocked_summary_row(s)
        for s in SCENARIOS
        if s.status in {"BLOCKED_NOT_APPROVED", "OPTIONAL_NOT_RUN"}
    ]
    if blocked_rows:
        summary = pd.concat([summary, pd.DataFrame(blocked_rows)], ignore_index=True)
    summary = summary.sort_values(
        by=["mandatory", "category", "scenario_id"],
        ascending=[False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    summary.to_csv(OUTPUT_DIR / OUTPUT_FILES["sensitivity_summary"], index=False)

    diagnostics_frame = pd.DataFrame(diagnostics_rows)
    diagnostics_frame.to_csv(
        OUTPUT_DIR / "scenario_diagnostics.csv", index=False
    )

    print("Hashing inputs after analyses ...")
    hashes_after = hash_inputs()

    print("Running independent validation ...")
    checks = run_stage6_checks(
        primary=primary,
        scenario_results=scenario_results,
        summary=summary,
        rankings=rankings,
        top10_frames=top10_frames,
        eligibility=eligibility,
        player_changes=player_changes,
        hashes_before=hashes_before,
        hashes_after=hashes_after,
        output_dir=OUTPUT_DIR,
        include_report=False,
    )

    print("Building report ...")
    report_text = build_sensitivity_report(
        summary=summary,
        top10_batter=top10_frames["batter"],
        top10_bowler=top10_frames["bowler"],
        eligibility=eligibility,
        player_changes=player_changes,
        checks=pd.DataFrame(checks),
        primary=primary,
        scenario_results=scenario_results,
        diagnostics=diagnostics_frame,
    )
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    # Report checks can only run after the report exists.  Append them and
    # rebuild the report so its stated validation count matches the CSV log.
    checks.extend(run_report_checks(summary, rankings))
    check_frame = pd.DataFrame(checks)
    check_frame.to_csv(OUTPUT_DIR / OUTPUT_FILES["validation_checks"], index=False)
    failed = check_frame[~check_frame["passed"].astype(bool)]
    print(f"Validation: {len(check_frame) - len(failed)}/{len(check_frame)} passed")
    report_text = build_sensitivity_report(
        summary=summary,
        top10_batter=top10_frames["batter"],
        top10_bowler=top10_frames["bowler"],
        eligibility=eligibility,
        player_changes=player_changes,
        checks=check_frame,
        primary=primary,
        scenario_results=scenario_results,
        diagnostics=diagnostics_frame,
    )
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    print(f"Wrote {OUTPUT_DIR}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Elapsed: {time.time() - start:.1f}s")
    if len(failed):
        for row in failed.itertuples(index=False):
            print(f"FAIL [{row.area}] {row.check}: {row.detail}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
