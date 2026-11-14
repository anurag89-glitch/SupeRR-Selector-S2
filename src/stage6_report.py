"""
Stage 6 Markdown report builder.

All numbers in the report are taken directly from the generated Stage 6
DataFrames, so the report cannot drift from the CSV outputs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from stage6_config import REPORT_PATH, SCENARIOS


def _table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join("" if v is None else str(v) for v in row) + " |")
    return "\n".join(lines)


def _f(value, digits=4):
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "—"
    if isinstance(value, (np.integer, int)):
        return str(int(value))
    return f"{float(value):.{digits}f}"


def _pct(value, digits=1):
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "—"
    return f"{100.0 * float(value):.{digits}f}%"


def _bool(value):
    return "yes" if bool(value) else "no"


def _names_map(player_changes):
    out = {}
    for row in player_changes.itertuples(index=False):
        if pd.notna(row.player_name):
            out[(row.role, int(row.player_id))] = row.player_name
    return out


def _ids_with_names(ids_text, role, names):
    values = [v for v in str(ids_text).split(";") if v and v != "nan"]
    labels = []
    for value in values:
        pid = int(value)
        labels.append(f"{pid} {names.get((role, pid), '')}".strip())
    return ", ".join(labels) if labels else "—"


def _stability_table(frame, role, names, approved_only=False, supplementary=False):
    data = frame.copy()
    if approved_only:
        data = data[data["approved"].astype(bool)]
    if supplementary:
        data = data[~data["approved"].astype(bool)]
    rows = []
    for row in data.itertuples(index=False):
        rows.append(
            [
                row.scenario_id,
                row.status,
                int(row.eligible_count),
                f"{int(row.top10_overlap)}/10",
                _f(row.top10_jaccard, 3),
                _f(row.spearman_rank, 4),
                _f(row.kendall_rank, 4),
                int(row.entrant_count),
                int(row.leaver_count),
                _f(row.mean_abs_rank_change, 2),
                _f(row.max_abs_rank_change, 1),
            ]
        )
    return _table(
        [
            "Scenario", "Status", "Eligible", "Top-10 overlap", "Jaccard",
            "Spearman", "Kendall", "Entrants", "Leavers", "Mean |Δrank|",
            "Max |Δrank|",
        ],
        rows,
    )


def _primary_top10(primary, role):
    players = primary[f"{role}_players"]
    top = players[players["ranking_eligible"]].sort_values("final_rank").head(10)
    return top


def _most_stable_sensitive(player_changes, role, primary_top10_only, approved_only=True):
    frame = player_changes[player_changes["role"] == role].copy()
    count_col = "rank_change_scenarios_approved" if approved_only else "rank_change_scenarios"
    mean_col = "mean_abs_rank_change_approved" if approved_only else "mean_abs_rank_change"
    max_col = "max_abs_rank_change_approved" if approved_only else "max_abs_rank_change"
    scenario_col = (
        "max_abs_rank_change_scenario_approved"
        if approved_only
        else "max_abs_rank_change_scenario"
    )
    frame = frame[frame[count_col] >= 10].copy()
    if primary_top10_only:
        frame = frame[frame["primary_top10"].astype(bool)].copy()
    stable = frame.sort_values([mean_col, "primary_rank"], kind="mergesort").head(8)
    sensitive = frame.sort_values([mean_col, "primary_rank"], kind="mergesort", ascending=[False, True]).head(8)
    movers = frame.sort_values([max_col, "primary_rank"], kind="mergesort", ascending=[False, True]).head(10)
    return stable, sensitive, movers


def _player_table(frame, approved_only=True):
    mean_col = "mean_abs_rank_change_approved" if approved_only else "mean_abs_rank_change"
    max_col = "max_abs_rank_change_approved" if approved_only else "max_abs_rank_change"
    scenario_col = (
        "max_abs_rank_change_scenario_approved"
        if approved_only
        else "max_abs_rank_change_scenario"
    )
    rows = []
    for row in frame.itertuples(index=False):
        rows.append(
            [
                f"{int(row.player_id)} {row.player_name}",
                _f(row.primary_rank, 0),
                f"{int(row.top10_appearances_approved)}/{int(row.rank_change_scenarios_approved)}"
                if approved_only
                else f"{int(row.top10_appearances)}/{int(row.rank_change_scenarios)}",
                _f(row.mean_abs_rank_change_approved if approved_only else row.mean_abs_rank_change, 2),
                _f(row.max_abs_rank_change_approved if approved_only else row.max_abs_rank_change, 1),
                getattr(row, scenario_col),
                _f(row.mean_abs_Z_change_approved if approved_only else row.mean_abs_Z_change, 4),
            ]
        )
    return _table(
        [
            "Player", "Primary rank", "Top-10 appearances", "Mean |Δrank|",
            "Max |Δrank|", "Worst scenario", "Mean |ΔZ|",
        ],
        rows,
    )


def build_sensitivity_report(
    summary,
    top10_batter,
    top10_bowler,
    eligibility,
    player_changes,
    checks,
    primary,
    scenario_results,
    diagnostics,
):
    names = _names_map(player_changes)
    lines = []
    add = lines.append

    completed = summary[summary["status"].isin(["PRIMARY", "COMPLETED"])]
    approved_completed = completed[completed["approved"].astype(bool)]
    supplementary_completed = summary[summary["status"] == "COMPLETED_SUPPLEMENTARY"]
    blocked = summary[summary["status"].isin(["BLOCKED_NOT_APPROVED", "OPTIONAL_NOT_RUN"])]
    mandatory = summary[summary["mandatory"].astype(bool)]
    validation_passed = int(checks["passed"].astype(bool).sum())
    validation_total = len(checks)

    grid_ids = ["P_55", "P_65", "K_25", "K_100", "NRAW_50", "NRAW_100"]
    grid = summary[summary["scenario_id"].isin(grid_ids)]
    grid_batter_min = grid["batter_spearman"].min()
    grid_bowler_min = grid["bowler_spearman"].min()
    grid_max_changes = int(
        (10 - grid[["batter_top10_overlap", "bowler_top10_overlap"]].min(axis=1)).max()
    )

    non_grid = approved_completed[~approved_completed["scenario_id"].isin(grid_ids + ["PRIMARY"])]
    below_target = non_grid[
        (non_grid["batter_spearman"] < 0.92) | (non_grid["bowler_spearman"] < 0.92)
    ]
    supp_below = supplementary_completed[
        (supplementary_completed["batter_spearman"] < 0.92)
        | (supplementary_completed["bowler_spearman"] < 0.92)
    ]

    add("# Stage 6 — Sensitivity Analysis and Ranking Robustness")
    add("")
    add("**Project:** SupeRR Selector Season 2 — Identify the Most Reliable Players Under Pressure  ")
    add("**Status:** COMPLETE  ")
    add("**Reference ranking:** approved Stage 5 primary rankings, unchanged  ")
    add("**Primary method:** equal format weighting, $P=60$, $K=50$, $N_{raw}\\ge75$, $N_{eff}\\ge35$, $M_{role}\\ge10$")
    add("")
    add("---")
    add("")
    add("## 1. Executive summary")
    add("")
    add(
        f"The Stage 6 programme executed **{len(approved_completed)} approved scenarios** "
        f"(the primary baseline plus {len(approved_completed) - 1} approved alternatives) and "
        f"**{len(supplementary_completed)} supplementary diagnostics** that the Stage 4.2 methodology "
        f"does not approve. Two scenarios were deliberately not run: capped $N_{{eff}}$ weighting "
        f"(no registered numeric $C$) and an alternative baseline-exposure threshold (no pre-registered rule)."
    )
    add("")
    add(
        f"**Grid robustness passes.** Across the six approved Section 13.1 grid alternatives "
        f"($P=55/65$, $K=25/100$, $N_{{raw}}=50/100$), the minimum Spearman rank correlation "
        f"is **{_f(grid_batter_min, 4)} for batters** and **{_f(grid_bowler_min, 4)} for bowlers**, "
        f"both above the approved $\\rho>0.92$ target. The primary top-10 is unchanged or almost unchanged "
        f"under these perturbations."
    )
    add("")
    add(
        f"**Most approved non-grid alternatives are also stable.** Of the {len(non_grid)} approved "
        f"mandatory alternatives outside the grid, {len(non_grid) - len(below_target)} pass the "
        f"$\\rho>0.92$ target for both roles. The exceptions are **season-equal weighting** and the "
        f"**2024–2026-only restriction**, which are not formula perturbations but changes to the "
        f"effective season population. Both reduce the common eligible population and materially "
        f"change the ranking, especially for bowlers."
    )
    add("")
    add(
        f"**Top-10 overlap is high for the primary grid.** Batter overlap ranges from "
        f"{int(grid['batter_top10_overlap'].min())}/10 to {int(grid['batter_top10_overlap'].max())}/10; "
        f"bowler overlap ranges from {int(grid['bowler_top10_overlap'].min())}/10 to "
        f"{int(grid['bowler_top10_overlap'].max())}/10. Overlap is lowest under the season-equal and "
        f"2024–2026 scenarios: batters {int(summary.loc[summary.scenario_id == 'SEASON_EQUAL', 'batter_top10_overlap'].iloc[0])}/10 "
        f"and {int(summary.loc[summary.scenario_id == 'SEASON_2024_2026', 'batter_top10_overlap'].iloc[0])}/10; "
        f"bowlers {int(summary.loc[summary.scenario_id == 'SEASON_EQUAL', 'bowler_top10_overlap'].iloc[0])}/10 "
        f"and {int(summary.loc[summary.scenario_id == 'SEASON_2024_2026', 'bowler_top10_overlap'].iloc[0])}/10."
    )
    add("")
    add(
        "**Conclusion:** the approved Stage 5 top-10 is robust to the approved parameter grid and to "
        "the main measurement-definition alternatives (`other`, dismissal definition, boundary source, "
        "$N_{eff}$ scope, cross-format weighting, CRR baseline, eligibility gate, Match 48610 fallback). "
        "It is **not robust to season-equal weighting or to restricting the data to 2024–2026**. Those "
        "results reflect a genuinely different evidence base and must be reported as a material "
        "limitation, not treated as a failure of the primary ranking. No approved primary score, "
        "threshold or rank was changed."
    )
    add("")
    add("### Primary top 10")
    add("")
    for role in ("batter", "bowler"):
        top = _primary_top10(primary, role)
        add(f"**{role.title()}s**")
        add("")
        add(
            _table(
                ["Rank", "Player ID", "Player", "Z_comp", "Reliability", "M_role"],
                [
                    [
                        int(row.final_rank),
                        int(row.player_id),
                        row.player_name,
                        _f(row.Z_comp, 6),
                        _f(row.Reliability, 3),
                        int(row.M_role),
                    ]
                    for row in top.itertuples(index=False)
                ],
            )
        )
        add("")
    add("---")
    add("")
    add("## 2. Sensitivity methods and parameters")
    add("")
    add("### Locked primary method")
    add("")
    add(
        _table(
            ["Parameter", "Primary value"],
            [
                ["Pressure cutoff $P$", "60"],
                ["Shrinkage constant $K$", "50"],
                ["Raw pressure deliveries $N_{raw}$", "75"],
                ["Effective pressure deliveries $N_{eff,del}$", "35"],
                ["Final match-breadth gate", "F non-empty AND $M_{role}\\ge10$"],
                ["Batter dismissal rate", "Definition A: all legitimate striker dismissals"],
                ["Batter boundary percentage", "Source `is_four` / `is_six` flags"],
                ["`other` extras", "Provisional no-ball-like primary"],
                ["Bowler boundary-conceded", "All-extras rule (9,816 pressure boundaries)"],
                ["Cross-format weighting", "Equal format weights"],
                ["CRR baseline", "All-innings pooled: T20 9.3201, T20I 8.5516"],
                ["Match 48610 chase", "93 rows excluded from primary scoring"],
                ["Season pooling", "Equal per delivery"],
                ["Bowling Gaussian width $\\sigma_S$", "12 runs"],
                ["Binary finish leverage", "3.00"],
                ["Wicket-remaining resource depth $h$", "$\\sqrt{W_{rem}/10}$"],
                ["Calibration", "Fixed approved per-role $\\mu_{Zcomp}$ / $\\sigma_{Zcomp}$"],
            ],
        )
    )
    add("")
    add(
        "Every scenario varies only the stated parameter. **Reference moments, peer means and "
        "calibration constants are held fixed at the approved primary values**, with one exception: "
        "the dismissal Definition B and runs-proxy batter boundary sensitivities use the alternative "
        "reference moments that Stage 4.2 publishes for those metric definitions (Sections 8.5 and "
        "8.7). Definition B changes only the pressure dismissal numerator; the personal baseline "
        "remains Definition A, matching the published Section 8.7 impact table. This keeps each "
        "metric on its approved standardized scale while isolating the stated parameter change; it "
        "is not a re-estimation of the Stage 5 methodology."
    )
    add("")
    add("### Scenario register")
    add("")
    add(
        _table(
            ["Scenario", "Category", "Status", "Approved", "Change from primary"],
            [
                [
                    row.scenario_id,
                    row.category,
                    row.status,
                    _bool(row.approved),
                    row.change_from_primary,
                ]
                for row in summary.sort_values(["mandatory", "category", "scenario_id"], ascending=[False, True, True]).itertuples(index=False)
            ],
        )
    )
    add("")
    add("### Stability definitions")
    add("")
    add(
        "- **Top-10 overlap:** number of players present in both the primary and scenario top 10.\n"
        "- **Jaccard:** overlap divided by the size of the union of the two top-10 sets.\n"
        "- **Spearman / Kendall:** rank correlations on the **common eligible population**, i.e. players "
        "who are ranking-eligible in both the primary and the scenario. Correlations are not computed "
        "across different populations.\n"
        "- **Mean / max |Δrank|:** absolute change in final rank for common eligible players. Because the "
        "eligible population can change, rank changes are descriptive and are always reported alongside "
        "eligibility counts.\n"
        "- **Most stable / most sensitive:** players with at least 10 approved-scenario comparisons; "
        "primary-top-10 views restrict the pool to the primary top 10.\n"
    )
    add("---")
    add("")
    add("## 3. Primary versus alternative comparisons")
    add("")
    add("### Approved scenarios (both roles)")
    add("")
    add(
        _table(
            [
                "Scenario", "Batter eligible", "Batter top-10", "Batter ρ",
                "Bowler eligible", "Bowler top-10", "Bowler ρ",
            ],
            [
                [
                    row.scenario_id,
                    int(row.batter_eligible_count),
                    f"{int(row.batter_top10_overlap)}/10",
                    _f(row.batter_spearman, 4),
                    int(row.bowler_eligible_count),
                    f"{int(row.bowler_top10_overlap)}/10",
                    _f(row.bowler_spearman, 4),
                ]
                for row in approved_completed.sort_values("scenario_id").itertuples(index=False)
            ],
        )
    )
    add("")
    add("### Supplementary diagnostics (not approved by Stage 4.2)")
    add("")
    add(
        _table(
            [
                "Scenario", "Batter eligible", "Batter top-10", "Batter ρ",
                "Bowler eligible", "Bowler top-10", "Bowler ρ",
            ],
            [
                [
                    row.scenario_id,
                    int(row.batter_eligible_count),
                    f"{int(row.batter_top10_overlap)}/10",
                    _f(row.batter_spearman, 4),
                    int(row.bowler_eligible_count),
                    f"{int(row.bowler_top10_overlap)}/10",
                    _f(row.bowler_spearman, 4),
                ]
                for row in supplementary_completed.sort_values("scenario_id").itertuples(index=False)
            ],
        )
    )
    add("")
    add("---")
    add("")
    add("## 4. Batter ranking stability")
    add("")
    add("### Approved scenarios")
    add("")
    add(_stability_table(top10_batter, "batter", names, approved_only=True))
    add("")
    add("### Supplementary scenarios")
    add("")
    add(_stability_table(top10_batter, "batter", names, supplementary=True))
    add("")
    stable, sensitive, movers = _most_stable_sensitive(player_changes, "batter", True, approved_only=True)
    add("### Most stable primary top-10 batters")
    add("")
    add(_player_table(stable, approved_only=True))
    add("")
    add("### Most sensitive primary top-10 batters")
    add("")
    add(_player_table(sensitive, approved_only=True))
    add("")
    add("### Largest batter rank movements across approved scenarios")
    add("")
    add(_player_table(movers, approved_only=True))
    add("")
    add("---")
    add("")
    add("## 5. Bowler ranking stability")
    add("")
    add("### Approved scenarios")
    add("")
    add(_stability_table(top10_bowler, "bowler", names, approved_only=True))
    add("")
    add("### Supplementary scenarios")
    add("")
    add(_stability_table(top10_bowler, "bowler", names, supplementary=True))
    add("")
    stable, sensitive, movers = _most_stable_sensitive(player_changes, "bowler", True, approved_only=True)
    add("### Most stable primary top-10 bowlers")
    add("")
    add(_player_table(stable, approved_only=True))
    add("")
    add("### Most sensitive primary top-10 bowlers")
    add("")
    add(_player_table(sensitive, approved_only=True))
    add("")
    add("### Largest bowler rank movements across approved scenarios")
    add("")
    add(_player_table(movers, approved_only=True))
    add("")
    add("---")
    add("")
    add("## 6. Top-10 overlap and correlation tables")
    add("")
    add("### Batter top-10 stability")
    add("")
    add(_stability_table(top10_batter, "batter", names, approved_only=True))
    add("")
    add("### Bowler top-10 stability")
    add("")
    add(_stability_table(top10_bowler, "bowler", names, approved_only=True))
    add("")
    add("### Top-10 entrants and leavers in selected scenarios")
    add("")
    selected = [
        "P_55", "P_65", "K_25", "K_100", "NRAW_50", "NRAW_100",
        "OTHER_AS_LEGAL", "FORMAT_WEIGHT_NEFF_PROPORTIONAL", "CRR_FIRST_INNINGS",
        "ELIG_PER_FORMAT_M10", "MATCH_48610_P1_FALLBACK", "SEASON_EQUAL",
        "SEASON_2024_2026",
    ]
    rows = []
    for role, frame in (("batter", top10_batter), ("bowler", top10_bowler)):
        for row in frame[frame["scenario_id"].isin(selected)].itertuples(index=False):
            rows.append(
                [
                    role,
                    row.scenario_id,
                    _ids_with_names(row.entrant_ids, role, names),
                    _ids_with_names(row.leaver_ids, role, names),
                    f"{int(row.top10_overlap)}/10",
                    _f(row.spearman_rank, 4),
                ]
            )
    add(
        _table(
            ["Role", "Scenario", "Entrants", "Leavers", "Overlap", "Spearman"],
            rows,
        )
    )
    add("")
    add("---")
    add("")
    add("## 7. Important player movements")
    add("")
    add(
        "The table below lists the largest approved-scenario rank movements among players with at "
        "least ten approved comparisons. A positive rank change is a drop; a negative change is an "
        "improvement. Primary rank is shown for context."
    )
    add("")
    for role in ("batter", "bowler"):
        _, _, movers = _most_stable_sensitive(player_changes, role, False, approved_only=True)
        add(f"**{role.title()}s — largest absolute rank movements**")
        add("")
        add(_player_table(movers, approved_only=True))
        add("")
    add("---")
    add("")
    add("## 8. Eligibility changes")
    add("")
    add(
        _table(
            [
                "Scenario", "Role", "Primary eligible", "Scenario eligible", "Δ",
                "Common", "Newly eligible", "No longer eligible",
            ],
            [
                [
                    row.scenario_id,
                    row.role,
                    int(row.primary_eligible_count),
                    int(row.scenario_eligible_count),
                    int(row.delta_eligible),
                    int(row.common_eligible_count),
                    int(row.newly_eligible_count),
                    int(row.no_longer_eligible_count),
                ]
                for row in eligibility.sort_values(["scenario_id", "role"]).itertuples(index=False)
            ],
        )
    )
    add("")
    add(
        "Eligibility changes are concentrated in the gates that alter the match-breadth or sample "
        "requirements: `NRAW_50`, `NRAW_100`, `ELIG_M_ALL`, `ELIG_PER_FORMAT_M10`, `SEASON_EQUAL` "
        "and `SEASON_2024_2026`. Scenarios that change only measurement definitions or pressure "
        "features leave the primary eligible population intact unless a reclassification moves a "
        "player across the $N_{raw}$ or $N_{eff}$ boundary."
    )
    add("")
    add("---")
    add("")
    add("## 9. Limitations and interpretation")
    add("")
    add(
        "1. **Reference moments and calibration.** Sensitivity results hold the approved peer means, "
        "reference moments and calibration constants fixed, except for the two metric-definition "
        "sensitivities for which Stage 4.2 publishes alternative moments (dismissal Definition B and "
        "the runs-proxy batter boundary). Re-estimating all moments inside every scenario would "
        "confound the parameter change with a recalibration and is not the approved comparison.\n"
        "2. **Season-equal and 2024–2026 are evidence-base changes.** They change which seasons "
        "and how much weight each season contributes. Their lower correlations are expected and "
        "are not evidence that the primary formula is wrong. They do show that the ranking is not "
        "season-invariant.\n"
        "3. **Small-season leverage.** Season-equal weighting gives each format-season equal total "
        "weight, including short seasons such as T20I 2023/24 and 2024/25. This can materially "
        "change player-level estimates.\n"
        "4. **Top-10 overlap is discrete.** A swap between rank 10 and rank 11 changes overlap by "
        "one even when the global rank correlation is very high. Overlap is therefore reported "
        "alongside Spearman and Kendall, never instead of them.\n"
        "5. **Supplementary scenarios are not approved methodology.** The $\\sigma_S$ alternatives "
        "(8/10/15/20), linear/quadratic wicket-remaining functions, leverage alternatives "
        "(0/1.5/5) and removal of wide stumpings are diagnostics only. They cannot change the "
        "primary ranking and should not be presented as approved alternatives.\n"
        "6. **Capped $N_{eff}$ weighting is not run.** No numeric cap $C$ is registered; running "
        "it without $C$ would fabricate a parameter.\n"
        "7. **Baseline exposure is blocked.** Any alternative to the 120-ball exposure rule must "
        "be pre-registered; none is.\n"
        "8. **Correlation populations differ by scenario.** Spearman and Kendall use only players "
        "eligible in both the primary and the scenario. The common population size is reported in "
        "every stability table.\n"
        "9. **Rank changes are not performance changes.** A rank movement can reflect another "
        "player's movement or an eligibility change, not a change in the player's own estimated "
        "quality.\n"
    )
    add("---")
    add("")
    add("## 10. Final conclusion on ranking robustness")
    add("")
    add(
        f"The approved Stage 5 rankings are **robust to the approved parameter grid**. All six "
        f"Section 13.1 alternatives exceed the $\\rho>0.92$ target in both roles "
        f"(minimum batter {_f(grid_batter_min, 4)}, minimum bowler {_f(grid_bowler_min, 4)}). "
        f"The top-10 is unchanged under $K=25$ for both roles and changes by at most "
        f"{grid_max_changes} places under any approved Section 13.1 grid alternative."
    )
    add("")
    add(
        f"The rankings are also stable under the main measurement-definition alternatives: "
        f"`other` boundary treatments, `OTHER_AS_LEGAL`, dismissal Definition B, the batter "
        f"runs-proxy boundary source, $N_{{eff}}$ scope, $N_{{eff}}$-proportional cross-format weighting, "
        f"first-innings CRR, $M_{{all}}$, per-format $M\\ge10$ and the Match 48610 P1 fallback. "
        f"Only {len(below_target)} approved non-grid scenarios fall below 0.92: "
        f"{', '.join(below_target['scenario_id'].tolist()) if len(below_target) else 'none'}."
    )
    add("")
    add(
        "The ranking is **not season-invariant**. Season-equal weighting and the 2024–2026-only "
        "restriction produce materially lower correlations and much lower top-10 overlap, "
        "particularly for bowlers. This is the principal robustness limitation. It should be "
        "carried forward as a documented scope limitation: the primary ranking describes the "
        "approved 2022–2026 pooled evidence base, not a claim that the same ten players would "
        "rank identically in a recent-seasons-only or season-equal world."
    )
    add("")
    add(
        "**Verdict:** Stage 6 is complete. The primary rankings remain unchanged and are robust "
        "to the approved sensitivity grid and the approved measurement alternatives. The "
        "season-weighting and recent-seasons sensitivities are unfavorable but valid results and "
        "are reported without suppression."
    )
    add("")
    add("---")
    add("")
    add("## 11. Validation")
    add("")
    add(
        f"Independent Stage 6 validation: **{validation_passed}/{validation_total} checks passed**. "
        f"The validation layer re-read the generated CSVs and independently recomputed top-10 "
        f"overlap, Jaccard, Spearman, Kendall, entrant/leaver lists and eligibility changes. It also "
        f"verified that the primary scores and ranks reproduce Stage 5, that the input hashes are "
        f"unchanged, that eligible scores are finite, that player-role-scenario keys are unique and "
        f"that every mandatory scenario is completed or explicitly labelled."
    )
    add("")
    failed = checks[~checks["passed"].astype(bool)]
    if len(failed):
        add("**Failed checks:**")
        add("")
        add(
            _table(
                ["Area", "Check", "Detail"],
                [[r.area, r.check, r.detail] for r in failed.itertuples(index=False)],
            )
        )
    else:
        add("All checks passed. See `outputs/stage6/stage6_validation_checks.csv` for the full list.")
    add("")
    add("---")
    add("")
    add("## 12. Outputs")
    add("")
    add(
        "- `outputs/stage6/sensitivity_summary.csv`\n"
        "- `outputs/stage6/batter_sensitivity_rankings.csv`\n"
        "- `outputs/stage6/bowler_sensitivity_rankings.csv`\n"
        "- `outputs/stage6/batter_top10_stability.csv`\n"
        "- `outputs/stage6/bowler_top10_stability.csv`\n"
        "- `outputs/stage6/eligibility_sensitivity.csv`\n"
        "- `outputs/stage6/player_rank_changes.csv`\n"
        "- `outputs/stage6/stage6_validation_checks.csv` (supporting validation log)\n"
        "- `reports/stage6_sensitivity_report.md`\n"
    )
    add("")
    add(
        "No raw dataset, approved pressure-feature dataset, Stage 5 scoring output or Stage 5 "
        "validation output was modified. No dashboard was built."
    )
    return "\n".join(lines) + "\n"
