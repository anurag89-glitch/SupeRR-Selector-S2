"""
Stage 6 independent validation.

The checks deliberately re-read the generated CSVs and the approved Stage 5
outputs instead of trusting the in-memory summary.  They verify parameter
registration, primary reproduction, score finiteness, rank uniqueness,
top-10 overlap, rank correlations, eligibility changes and input integrity.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

from stage5_config import (
    MATCH_GATE,
    NEFF_GATE,
    OUTPUT_DIR as STAGE5_OUTPUT_DIR,
    PRESSURE_CUTOFF,
    RAW_GATE,
    REFERENCE_MOMENTS,
    SHRINKAGE_K,
)
from stage6_config import (
    OUTPUT_FILES,
    OUTPUT_DIR,
    REPORT_PATH,
    SCENARIOS,
    SCENARIO_BY_ID,
    SENSITIVITY_REFERENCE_MOMENTS,
)

TOL = 1e-8


def _add(checks, area, check, passed, detail=""):
    checks.append(
        {
            "area": area,
            "check": check,
            "passed": bool(passed),
            "detail": str(detail),
        }
    )


def _max_abs_diff(a, b) -> float:
    a = pd.to_numeric(pd.Series(a), errors="coerce").to_numpy(dtype=float)
    b = pd.to_numeric(pd.Series(b), errors="coerce").to_numpy(dtype=float)
    if len(a) != len(b):
        return float("inf")
    mask = np.isfinite(a) & np.isfinite(b)
    if not mask.any():
        return 0.0
    return float(np.max(np.abs(a[mask] - b[mask])))


def _ids(values) -> list[int]:
    return [int(v) for v in values if pd.notna(v)]


def _check_registry(checks):
    required = {
        "PRIMARY", "P_55", "P_65", "K_25", "K_100", "NRAW_50", "NRAW_100",
        "WKT_RATE_NEFF_ALL_DELIVERIES", "DISMISSAL_RATE_WIDE_EXCLUDED",
        "BOUNDARY_RUNS_PROXY", "OTHER_BOUNDARY_LEGAL_OVERSTEP",
        "OTHER_BOUNDARY_LEGAL_ONLY", "OTHER_AS_LEGAL",
        "FORMAT_WEIGHT_NEFF_PROPORTIONAL", "CRR_FIRST_INNINGS",
        "ELIG_M_ALL", "ELIG_PER_FORMAT_M10", "NEFF_SCOPE_ALL_DELIVERIES",
        "MATCH_48610_P1_FALLBACK", "SEASON_EQUAL", "SEASON_2024_2026",
        "SUPP_SIGMA_8", "SUPP_SIGMA_10", "SUPP_SIGMA_15", "SUPP_SIGMA_20",
        "SUPP_H_LINEAR", "SUPP_H_QUADRATIC", "SUPP_LEVERAGE_0",
        "SUPP_LEVERAGE_1_5", "SUPP_LEVERAGE_5", "SUPP_WIDE_STUMP_REMOVED",
        "OPTIONAL_NEFF_CAPPED", "BASELINE_EXPOSURE_ALT",
    }
    present = {s.scenario_id for s in SCENARIOS}
    _add(
        checks,
        "Scenario registry",
        "All required mandatory, supplementary and blocked scenarios are registered",
        required == present,
        f"missing={sorted(required - present)} extra={sorted(present - required)}",
    )

    expected = {
        "PRIMARY": dict(
            pressure_cutoff=60.0, shrinkage_k=50.0, raw_gate=75,
            neff_gate=35.0, match_gate=10, sigma=12.0, leverage=3.0,
            h_mode="sqrt", crr_source="all_innings",
            include_48610_chase=False, dismissal_definition="A",
            boundary_source="flags", boundary_legality="all",
            other_as_legal=False, wicket_neff="legal", neff_scope="primary",
            wide_stump_action="retain", cross_format_weight="equal",
            eligibility="primary", season_weight="delivery", season_from=None,
        ),
        "P_55": dict(pressure_cutoff=55.0),
        "P_65": dict(pressure_cutoff=65.0),
        "K_25": dict(shrinkage_k=25.0),
        "K_100": dict(shrinkage_k=100.0),
        "NRAW_50": dict(raw_gate=50),
        "NRAW_100": dict(raw_gate=100),
        "WKT_RATE_NEFF_ALL_DELIVERIES": dict(wicket_neff="all_deliveries"),
        "DISMISSAL_RATE_WIDE_EXCLUDED": dict(dismissal_definition="B"),
        "BOUNDARY_RUNS_PROXY": dict(boundary_source="runs"),
        "OTHER_BOUNDARY_LEGAL_OVERSTEP": dict(boundary_legality="legal_overstep"),
        "OTHER_BOUNDARY_LEGAL_ONLY": dict(boundary_legality="legal"),
        "OTHER_AS_LEGAL": dict(other_as_legal=True),
        "FORMAT_WEIGHT_NEFF_PROPORTIONAL": dict(cross_format_weight="neff"),
        "CRR_FIRST_INNINGS": dict(crr_source="first_innings"),
        "ELIG_M_ALL": dict(eligibility="m_all"),
        "ELIG_PER_FORMAT_M10": dict(eligibility="per_format_m10"),
        "NEFF_SCOPE_ALL_DELIVERIES": dict(neff_scope="all_deliveries"),
        "MATCH_48610_P1_FALLBACK": dict(include_48610_chase=True),
        "SEASON_EQUAL": dict(season_weight="equal"),
        "SEASON_2024_2026": dict(season_from=2024),
        "SUPP_SIGMA_8": dict(sigma=8.0),
        "SUPP_SIGMA_10": dict(sigma=10.0),
        "SUPP_SIGMA_15": dict(sigma=15.0),
        "SUPP_SIGMA_20": dict(sigma=20.0),
        "SUPP_H_LINEAR": dict(h_mode="linear"),
        "SUPP_H_QUADRATIC": dict(h_mode="quadratic"),
        "SUPP_LEVERAGE_0": dict(leverage=0.0),
        "SUPP_LEVERAGE_1_5": dict(leverage=1.5),
        "SUPP_LEVERAGE_5": dict(leverage=5.0),
        "SUPP_WIDE_STUMP_REMOVED": dict(wide_stump_action="remove"),
    }
    failures = []
    for scenario_id, fields in expected.items():
        scenario = SCENARIO_BY_ID[scenario_id]
        for field, expected_value in fields.items():
            got = getattr(scenario, field)
            if isinstance(expected_value, float):
                ok = abs(float(got) - expected_value) < 1e-12
            else:
                ok = got == expected_value
            if not ok:
                failures.append(f"{scenario_id}.{field}={got!r} != {expected_value!r}")
    _add(
        checks,
        "Scenario parameters",
        "Every executed sensitivity uses its registered approved parameter value",
        not failures,
        "; ".join(failures) if failures else f"{len(expected)} scenario parameter maps checked",
    )

    blocked = [s for s in SCENARIOS if not s.mandatory and s.status != "COMPLETED_SUPPLEMENTARY"]
    _add(
        checks,
        "Scenario registry",
        "Optional capped N_eff and unregistered baseline-exposure scenarios are not executed",
        all(s.status in {"OPTIONAL_NOT_RUN", "BLOCKED_NOT_APPROVED"} and s.blocked_reason for s in blocked),
        ", ".join(f"{s.scenario_id}: {s.status}" for s in blocked),
    )


def _check_primary(primary, checks):
    stage5 = STAGE5_OUTPUT_DIR
    for role in ("batter", "bowler"):
        got = primary[f"{role}_players"].copy()
        exp = pd.read_csv(stage5 / f"{role}_scoring.csv")
        merged = got.merge(exp, on="player_id", suffixes=("_g", "_e"), how="outer", indicator=True)
        both = merged[merged["_merge"] == "both"]
        got_ids = set(got.loc[got["ranking_eligible"], "player_id"])
        exp_ids = set(exp.loc[exp["ranking_eligible"], "player_id"])
        same_pop = got_ids == exp_ids
        rank_ok = True
        if same_pop:
            ge = both[both["ranking_eligible_g"].astype(bool)]
            rank_ok = (
                ge["final_rank_g"].astype(float).tolist()
                == ge["final_rank_e"].astype(float).tolist()
            )
        z_diff = _max_abs_diff(both["Z_comp_g"], both["Z_comp_e"])
        rel_diff = _max_abs_diff(both["Reliability_g"], both["Reliability_e"])
        m_ok = bool((both["M_role_g"].astype(int) == both["M_role_e"].astype(int)).all())
        top_got = got[got["ranking_eligible"]].sort_values("final_rank").head(10)["player_id"].tolist()
        top_exp = exp[exp["ranking_eligible"]].sort_values("final_rank").head(10)["player_id"].tolist()
        _add(
            checks,
            "Primary reproduction",
            f"{role.title()} primary eligible set and ranks reproduce Stage 5 exactly",
            same_pop and rank_ok,
            f"n={len(got_ids)}/{len(exp_ids)}; ids_equal={same_pop}; ranks_equal={rank_ok}",
        )
        _add(
            checks,
            "Primary reproduction",
            f"{role.title()} primary Z_comp, Reliability and M_role reproduce Stage 5",
            z_diff < TOL and rel_diff < TOL and m_ok,
            f"max_Z_diff={z_diff:.3e}; max_Rel_diff={rel_diff:.3e}; M_equal={m_ok}",
        )
        _add(
            checks,
            "Primary reproduction",
            f"{role.title()} primary top-10 matches the Stage 5 top-10 CSV",
            top_got == top_exp,
            f"top10={top_got}",
        )

    for role, filename in (
        ("batter", "batter_format_records.csv"),
        ("bowler", "bowler_format_records.csv"),
    ):
        got = primary[f"{role}_records"]
        exp = pd.read_csv(STAGE5_OUTPUT_DIR / filename)
        merged = got.merge(
            exp, on=["match_format", "player_id"], suffixes=("_g", "_e"),
            how="outer", indicator=True,
        )
        both = merged[merged["_merge"] == "both"]
        keys = [
            "N_raw", "N_eff_del", "Z_comp_format", "N_eff_BF", "N_eff_legal",
            "SR_P", "Boundary_P", "Dot_P", "DR_P", "Econ_P", "WktRate_P",
            "Dot_bowl_P", "BoundaryConc_P",
        ]
        diffs = {
            key: _max_abs_diff(both[key + "_g"], both[key + "_e"])
            for key in keys
            if key + "_g" in both and key + "_e" in both
        }
        worst = max(diffs.values()) if diffs else 0.0
        _add(
            checks,
            "Primary reproduction",
            f"{role.title()} format records reproduce Stage 5 (max abs diff < {TOL:g})",
            len(merged) == len(exp) and len(merged) == len(got) and worst < TOL,
            f"records={len(got)}; merge={merged['_merge'].value_counts().to_dict()}; worst_diff={worst:.3e}",
        )


def _check_hashes(hashes_before, hashes_after, checks):
    changed = sorted(
        key for key in hashes_before if hashes_before[key] != hashes_after.get(key)
    )
    added = sorted(set(hashes_after) - set(hashes_before))
    _add(
        checks,
        "Input integrity",
        "Raw datasets, approved pressure features and Stage 5 outputs are unchanged",
        not changed and not added,
        f"changed={changed}; added={added}",
    )


def _check_outputs(output_dir: Path, checks, include_report: bool = True):
    required = {
        "sensitivity_summary": 33,
        "batter_sensitivity_rankings": 1,
        "bowler_sensitivity_rankings": 1,
        "batter_top10_stability": 1,
        "bowler_top10_stability": 1,
        "eligibility_sensitivity": 1,
        "player_rank_changes": 1,
    }
    failures = []
    for key, min_rows in required.items():
        path = output_dir / OUTPUT_FILES[key]
        if not path.exists():
            failures.append(f"{key}: missing")
            continue
        if path.stat().st_size == 0:
            failures.append(f"{key}: empty")
            continue
        try:
            frame = pd.read_csv(path)
        except Exception as exc:  # pragma: no cover - defensive
            failures.append(f"{key}: unreadable ({exc})")
            continue
        if len(frame) < min_rows:
            failures.append(f"{key}: {len(frame)} rows < {min_rows}")
    _add(
        checks,
        "Output files",
        "All seven required Stage 6 CSVs exist, are readable and contain data",
        not failures,
        "; ".join(failures) if failures else "7 required CSVs checked",
    )

    if include_report:
        report = REPORT_PATH
        _add(
            checks,
            "Output files",
            "Stage 6 Markdown report exists and is non-empty",
            report.exists() and report.stat().st_size > 0,
            f"{report} ({report.stat().st_size if report.exists() else 0} bytes)",
        )


def _check_rankings_valid(rankings, checks):
    failures = []
    for role, frame in rankings.items():
        required_cols = {
            "scenario_id", "role", "player_id", "ranking_eligible", "final_rank",
            "Z_comp", "Z_std", "Reliability", "primary_rank",
            "rank_change_vs_primary",
        }
        missing = required_cols - set(frame.columns)
        if missing:
            failures.append(f"{role}: missing columns {sorted(missing)}")
            continue
        if frame.duplicated(["scenario_id", "role", "player_id"]).any():
            failures.append(f"{role}: duplicate scenario/role/player")
        eligible = frame[frame["ranking_eligible"].astype(bool)]
        if eligible.duplicated(["scenario_id", "final_rank"]).any():
            failures.append(f"{role}: duplicate scenario/final_rank")
        for col in ("Z_comp", "Z_std", "Reliability"):
            if not np.isfinite(eligible[col].astype(float)).all():
                failures.append(f"{role}: non-finite {col}")
        if not eligible["Reliability"].between(0, 100).all():
            failures.append(f"{role}: Reliability outside 0-100")
        for sid, group in eligible.groupby("scenario_id"):
            ranks = sorted(group["final_rank"].astype(int).tolist())
            if ranks != list(range(1, len(ranks) + 1)):
                failures.append(f"{role}/{sid}: ranks not contiguous")
    _add(
        checks,
        "Ranking validity",
        "No duplicate player-role-scenario rows; eligible scores finite and ranks contiguous",
        not failures,
        "; ".join(failures) if failures else "all scenario ranking tables checked",
    )


def _check_primary_thresholds(primary, rankings, checks):
    failures = []
    for role in ("batter", "bowler"):
        players = primary[f"{role}_players"]
        eligible = players[players["ranking_eligible"]]
        if not (eligible["M_role"] >= MATCH_GATE).all():
            failures.append(f"{role}: M_role gate violated")
        records = primary[f"{role}_records"]
        ready = records[records["composite_ready"]]
        if not (ready["N_raw"] >= RAW_GATE).all():
            failures.append(f"{role}: N_raw gate violated")
        if not (ready["N_eff_del"] >= NEFF_GATE).all():
            failures.append(f"{role}: N_eff gate violated")
        if not (ready["baseline_ok"].astype(bool)).all():
            failures.append(f"{role}: baseline gate violated")
    _add(
        checks,
        "Eligibility thresholds",
        "Primary N_raw>=75, N_eff>=35, baseline>=120 and M_role>=10 gates are unchanged",
        not failures,
        "; ".join(failures) if failures else "all four primary gates verified",
    )

    # Scenario gates must match their declared policy.
    failures = []
    for sid, group in rankings["batter"].groupby("scenario_id"):
        scenario = SCENARIO_BY_ID[sid]
        elig = group[group["ranking_eligible"].astype(bool)]
        if scenario.eligibility == "m_all":
            if not (elig["M_all"].astype(int) >= scenario.match_gate).all():
                failures.append(f"{sid}: M_all gate")
        else:
            if not (elig["M_role"].astype(int) >= scenario.match_gate).all():
                failures.append(f"{sid}: M_role gate")
    for sid, group in rankings["bowler"].groupby("scenario_id"):
        scenario = SCENARIO_BY_ID[sid]
        elig = group[group["ranking_eligible"].astype(bool)]
        if scenario.eligibility == "m_all":
            if not (elig["M_all"].astype(int) >= scenario.match_gate).all():
                failures.append(f"{sid}: M_all gate")
        else:
            if not (elig["M_role"].astype(int) >= scenario.match_gate).all():
                failures.append(f"{sid}: M_role gate")
    _add(
        checks,
        "Eligibility thresholds",
        "Each scenario applies its declared M_role / M_all eligibility rule",
        not failures,
        "; ".join(failures) if failures else "all scenario eligibility rules verified",
    )


def _check_sensitivity_moments(primary, scenario_results, checks):
    """Verify published alternative moments and declared role/metric scope."""
    failures = []
    for scenario_id, overrides in SENSITIVITY_REFERENCE_MOMENTS.items():
        result = scenario_results.get(scenario_id)
        if result is None:
            failures.append(f"{scenario_id}: missing result")
            continue
        records = result["batter_records"]
        for (role, fmt, metric), (mean, sd) in overrides.items():
            subset = records[records["match_format"] == fmt]
            if subset.empty:
                failures.append(f"{scenario_id}/{fmt}/{metric}: empty format")
                continue
            expected_z = (subset[f"shrunk_{metric}"].astype(float) - mean) / sd
            diff = _max_abs_diff(subset[f"z_{metric}"], expected_z)
            if diff > 1e-10:
                failures.append(
                    f"{scenario_id}/{fmt}/{metric}: z formula diff {diff:.3e}"
                )
            primary_mean, primary_sd = REFERENCE_MOMENTS[(role, fmt, metric)]
            if abs(mean - primary_mean) < 1e-12 and abs(sd - primary_sd) < 1e-12:
                failures.append(
                    f"{scenario_id}/{fmt}/{metric}: override equals primary moments"
                )

        if scenario_id == "DISMISSAL_RATE_WIDE_EXCLUDED":
            # Stage 4.2 Section 8.7 changes only the pressure numerator in
            # Definition B.  The personal baseline remains Definition A.
            primary_batters = primary["batter_records"][
                ["match_format", "player_id", "DR_base"]
            ]
            merged = records.merge(
                primary_batters,
                on=["match_format", "player_id"],
                suffixes=("", "_primary"),
            )
            diff = _max_abs_diff(merged["DR_base"], merged["DR_base_primary"])
            if diff > 1e-12:
                failures.append(
                    f"{scenario_id}: baseline DR changed (max diff {diff:.3e})"
                )
            for fmt, (mean, sd) in (
                (fmt, moment)
                for (_role, fmt, metric), moment in overrides.items()
                if metric == "dDR"
            ):
                subset = merged[merged["match_format"] == fmt].copy()
                subset = subset[
                    (subset["N_raw"] >= RAW_GATE)
                    & (subset["N_eff_del"] >= NEFF_GATE)
                    & (subset["sum_wbf"] > 0)
                    & subset["baseline_ok"].astype(bool)
                    & np.isfinite(subset["shrunk_dDR"])
                ]
                got_mean = float(subset["shrunk_dDR"].mean())
                got_sd = float(subset["shrunk_dDR"].std(ddof=0))
                if abs(got_mean - mean) > 1e-6 or abs(got_sd - sd) > 1e-6:
                    failures.append(
                        f"{scenario_id}/{fmt}: published moments reproduced "
                        f"as ({got_mean:.6f}, {got_sd:.6f}), expected "
                        f"({mean:.6f}, {sd:.6f})"
                    )

        # These two definition changes are batter-only.  Bowler scores and
        # ranks must remain exactly the primary bowler scores and ranks.
        got = result["bowler_players"]
        exp = primary["bowler_players"]
        merged = got.merge(exp, on="player_id", suffixes=("_g", "_e"))
        got_ids = set(got.loc[got["ranking_eligible"], "player_id"])
        exp_ids = set(exp.loc[exp["ranking_eligible"], "player_id"])
        if got_ids != exp_ids:
            failures.append(f"{scenario_id}: bowler eligible set changed")
            continue
        both = merged[
            merged["ranking_eligible_g"].astype(bool)
            & merged["ranking_eligible_e"].astype(bool)
        ]
        if _max_abs_diff(both["Z_comp_g"], both["Z_comp_e"]) > 1e-12:
            failures.append(f"{scenario_id}: bowler Z_comp changed")
        if not (
            both["final_rank_g"].astype(int).to_numpy()
            == both["final_rank_e"].astype(int).to_numpy()
        ).all():
            failures.append(f"{scenario_id}: bowler ranks changed")

    _add(
        checks,
        "Sensitivity moments",
        "Definition B and runs-proxy use the published alternative moments and leave bowler scores unchanged",
        not failures,
        "; ".join(failures)
        if failures
        else "2 metric-definition sensitivities and 4 alternative format-metric moments verified",
    )


def _recompute_top10_metrics(rankings, role):
    frame = rankings[role]
    primary = pd.read_csv(STAGE5_OUTPUT_DIR / f"{role}_scoring.csv")
    primary_top = primary[primary["ranking_eligible"].astype(bool)].sort_values("final_rank").head(10)["player_id"].tolist()
    primary_map = (
        primary[primary["ranking_eligible"].astype(bool)]
        .set_index("player_id")["final_rank"]
        .astype(float)
        .to_dict()
    )
    rows = []
    for sid, group in frame.groupby("scenario_id"):
        eligible = group[group["ranking_eligible"].astype(bool)].copy()
        if eligible.empty:
            continue
        scenario_top = eligible.sort_values("final_rank").head(10)["player_id"].tolist()
        overlap = len(set(primary_top) & set(scenario_top))
        union = set(primary_top) | set(scenario_top)
        common = eligible[eligible["player_id"].isin(primary_map)].copy()
        common["primary_rank_calc"] = common["player_id"].map(primary_map)
        common["scenario_rank_calc"] = common["final_rank"].astype(float)
        rho = np.nan
        tau = np.nan
        if len(common) >= 3:
            rho = float(spearmanr(common["primary_rank_calc"], common["scenario_rank_calc"]).statistic)
            tau = float(kendalltau(common["primary_rank_calc"], common["scenario_rank_calc"]).statistic)
        rows.append(
            {
                "scenario_id": sid,
                "top10_overlap": overlap,
                "top10_jaccard": overlap / len(union) if union else np.nan,
                "spearman_rank": rho,
                "kendall_rank": tau,
                "common_n": len(common),
                "entrant_ids": sorted(set(scenario_top) - set(primary_top)),
                "leaver_ids": sorted(set(primary_top) - set(scenario_top)),
            }
        )
    return pd.DataFrame(rows)


def _check_top10_and_eligibility(summary, rankings, top10_frames, eligibility, checks):
    failures = []
    for role in ("batter", "bowler"):
        calc = _recompute_top10_metrics(rankings, role)
        stored = top10_frames[role].set_index("scenario_id")
        for row in calc.itertuples(index=False):
            sid = row.scenario_id
            if sid not in stored.index:
                failures.append(f"{role}/{sid}: missing top10 row")
                continue
            srow = stored.loc[sid]
            if int(srow["top10_overlap"]) != int(row.top10_overlap):
                failures.append(f"{role}/{sid}: overlap {srow['top10_overlap']} != {row.top10_overlap}")
            if abs(float(srow["top10_jaccard"]) - float(row.top10_jaccard)) > 1e-12:
                failures.append(f"{role}/{sid}: jaccard")
            for col in ("spearman_rank", "kendall_rank"):
                a = float(srow[col])
                b = float(getattr(row, col))
                if np.isfinite(a) and np.isfinite(b):
                    if abs(a - b) > 1e-10:
                        failures.append(f"{role}/{sid}: {col} {a} != {b}")
                elif not (np.isnan(a) and np.isnan(b)):
                    failures.append(f"{role}/{sid}: {col} NaN mismatch")
            if int(srow["common_n"]) != int(row.common_n):
                failures.append(f"{role}/{sid}: common_n")
            stored_ent = {int(v) for v in str(srow["entrant_ids"]).split(";") if v and v != "nan"}
            stored_lev = {int(v) for v in str(srow["leaver_ids"]).split(";") if v and v != "nan"}
            if stored_ent != set(row.entrant_ids):
                failures.append(f"{role}/{sid}: entrants")
            if stored_lev != set(row.leaver_ids):
                failures.append(f"{role}/{sid}: leavers")
        # Summary must agree with the stability table.
        for sid in calc["scenario_id"]:
            srow = summary[summary["scenario_id"] == sid]
            trow = stored.loc[sid]
            if len(srow) != 1:
                failures.append(f"summary/{sid}: not exactly one row")
                continue
            srow = srow.iloc[0]
            if int(srow[f"{role}_top10_overlap"]) != int(trow["top10_overlap"]):
                failures.append(f"summary/{role}/{sid}: overlap")
            if abs(float(srow[f"{role}_spearman"]) - float(trow["spearman_rank"])) > 1e-10:
                failures.append(f"summary/{role}/{sid}: spearman")
            if int(srow[f"{role}_entrants"]) != int(trow["entrant_count"]):
                failures.append(f"summary/{role}/{sid}: entrants")
            if int(srow[f"{role}_leavers"]) != int(trow["leaver_count"]):
                failures.append(f"summary/{role}/{sid}: leavers")
    _add(
        checks,
        "Top-10 stability",
        "Top-10 overlap, Jaccard, Spearman, Kendall and entrant/leaver lists recompute exactly from CSVs",
        not failures,
        "; ".join(failures) if failures else "all completed scenarios independently recomputed",
    )

    failures = []
    for role in ("batter", "bowler"):
        primary = pd.read_csv(STAGE5_OUTPUT_DIR / f"{role}_scoring.csv")
        p_ids = set(primary.loc[primary["ranking_eligible"].astype(bool), "player_id"].astype(int))
        frame = rankings[role]
        for row in eligibility[eligibility["role"] == role].itertuples(index=False):
            sid = row.scenario_id
            group = frame[frame["scenario_id"] == sid]
            s_ids = set(group.loc[group["ranking_eligible"].astype(bool), "player_id"].astype(int))
            newly = set(_ids(str(row.newly_eligible_ids).split(";"))) if isinstance(row.newly_eligible_ids, str) and row.newly_eligible_ids else set()
            lost = set(_ids(str(row.no_longer_eligible_ids).split(";"))) if isinstance(row.no_longer_eligible_ids, str) and row.no_longer_eligible_ids else set()
            if int(row.primary_eligible_count) != len(p_ids):
                failures.append(f"{role}/{sid}: primary count")
            if int(row.scenario_eligible_count) != len(s_ids):
                failures.append(f"{role}/{sid}: scenario count")
            if int(row.common_eligible_count) != len(p_ids & s_ids):
                failures.append(f"{role}/{sid}: common count")
            if newly != (s_ids - p_ids):
                failures.append(f"{role}/{sid}: newly eligible IDs")
            if lost != (p_ids - s_ids):
                failures.append(f"{role}/{sid}: lost eligible IDs")
    _add(
        checks,
        "Eligibility sensitivity",
        "Eligible counts, newly eligible players and no-longer-eligible players recompute from CSVs",
        not failures,
        "; ".join(failures) if failures else "all eligibility comparisons verified",
    )


def _check_scenario_completeness(summary, checks):
    missing = []
    bad_status = []
    for scenario in SCENARIOS:
        row = summary[summary["scenario_id"] == scenario.scenario_id]
        if len(row) != 1:
            missing.append(scenario.scenario_id)
            continue
        status = row.iloc[0]["status"]
        if status != scenario.status:
            bad_status.append(f"{scenario.scenario_id}: {status} != {scenario.status}")
    mandatory_bad = summary[
        (summary["mandatory"].astype(bool))
        & (~summary["status"].isin(["PRIMARY", "COMPLETED"]))
    ]
    _add(
        checks,
        "Completeness",
        "Every registered scenario has exactly one summary row and the declared status",
        not missing and not bad_status,
        f"missing={missing}; status_mismatch={bad_status}",
    )
    _add(
        checks,
        "Completeness",
        "All mandatory approved scenarios are completed; blocked scenarios are explicitly labelled",
        mandatory_bad.empty,
        "all mandatory scenarios completed"
        if mandatory_bad.empty
        else mandatory_bad[["scenario_id", "status", "blocked_reason"]].to_string(index=False),
    )


def _check_scenario_diagnostics(summary, diagnostics, checks):
    failures = []
    lookup = summary.set_index("scenario_id")
    diag = diagnostics.set_index("scenario_id")
    # Approved boundary counts.
    expected = {
        "PRIMARY": (9816, 9790, 9756),
        "OTHER_BOUNDARY_LEGAL_OVERSTEP": (9790, 9790, 9756),
        "OTHER_BOUNDARY_LEGAL_ONLY": (9756, 9756, 9756),
        "MATCH_48610_P1_FALLBACK": (9827, 9801, 9767),
    }
    for sid, counts in expected.items():
        if sid not in lookup.index:
            failures.append(f"{sid}: missing summary")
            continue
        row = lookup.loc[sid]
        got = (
            int(row["boundary_count_all"]),
            int(row["boundary_count_legal_overstep"]),
            int(row["boundary_count_legal_only"]),
        )
        if got != counts:
            failures.append(f"{sid}: boundary counts {got} != {counts}")
    if "PRIMARY" in diag.index:
        if int(diag.loc["PRIMARY", "corpus_rows"]) != 191_963:
            failures.append("PRIMARY corpus rows")
        if int(diag.loc["PRIMARY", "matches"]) != 812:
            failures.append("PRIMARY match count")
        if int(diag.loc["PRIMARY", "other_rows"]) != 256:
            failures.append("PRIMARY other rows")
        if int(diag.loc["PRIMARY", "widestump_pressure_rows"]) != 6:
            failures.append("PRIMARY wide-stump pressure rows")
    if "MATCH_48610_P1_FALLBACK" in diag.index:
        if int(diag.loc["MATCH_48610_P1_FALLBACK", "corpus_rows"]) != 192_056:
            failures.append("fallback corpus rows")
    if "OTHER_AS_LEGAL" in diag.index:
        if int(diag.loc["OTHER_AS_LEGAL", "other_rows"]) != 256:
            failures.append("OTHER_AS_LEGAL other rows")
        if int(diag.loc["OTHER_AS_LEGAL", "other_legal_rows"]) != 256:
            failures.append("OTHER_AS_LEGAL legal other rows")
    if "SEASON_2024_2026" in diag.index:
        if int(diag.loc["SEASON_2024_2026", "corpus_rows"]) != 117_195:
            failures.append("2024-2026 corpus rows")
    _add(
        checks,
        "Scenario diagnostics",
        "Corpus sizes, boundary treatments, other-as-legal and Match 48610 fallback signatures match the approved rules",
        not failures,
        "; ".join(failures) if failures else "all scenario signatures verified",
    )


def _check_report(summary, rankings, checks):
    if not REPORT_PATH.exists():
        _add(checks, "Report", "Report exists", False, "missing")
        return
    text = REPORT_PATH.read_text(encoding="utf-8")
    missing = [sid for sid in summary["scenario_id"] if sid not in text]
    primary_top = {}
    for role in ("batter", "bowler"):
        frame = rankings[role]
        row = frame[(frame["scenario_id"] == "PRIMARY") & (frame["ranking_eligible"].astype(bool))]
        primary_top[role] = [str(int(v)) for v in row.sort_values("final_rank").head(10)["player_id"]]
    id_missing = {
        role: [pid for pid in ids if pid not in text]
        for role, ids in primary_top.items()
    }
    _add(
        checks,
        "Report",
        "Report mentions every registered scenario and both primary top-10 lists",
        not missing and not any(id_missing.values()),
        f"missing_scenarios={missing}; missing_top_ids={id_missing}",
    )


def run_stage6_checks(
    primary,
    scenario_results,
    summary,
    rankings,
    top10_frames,
    eligibility,
    player_changes,
    hashes_before,
    hashes_after,
    output_dir,
    include_report: bool = True,
):
    checks = []
    _check_registry(checks)
    _check_primary(primary, checks)
    _check_hashes(hashes_before, hashes_after, checks)
    _check_outputs(output_dir, checks, include_report=include_report)
    _check_rankings_valid(rankings, checks)
    _check_primary_thresholds(primary, rankings, checks)
    _check_sensitivity_moments(primary, scenario_results, checks)
    _check_top10_and_eligibility(summary, rankings, top10_frames, eligibility, checks)
    _check_scenario_completeness(summary, checks)
    diagnostics = pd.DataFrame(
        [result["diagnostics"] for result in scenario_results.values()]
    )
    _check_scenario_diagnostics(summary, diagnostics, checks)
    if include_report:
        _check_report(summary, rankings, checks)
    return checks


def run_report_checks(summary, rankings):
    """Report-only checks, run after the report has been written."""
    checks = []
    _check_report(summary, rankings, checks)
    return checks
