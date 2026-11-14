"""
Stage 6 sensitivity tests.

These tests exercise the parameterized scoring engine, the registered scenario
set, the approved primary reproduction, the season-equal weights, the `other`
and boundary treatments, the scenario eligibility gates and the stability
helpers.  They deliberately do not write any output file.
"""

from __future__ import annotations

import dataclasses
import re
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stage5_config import (  # noqa: E402
    MATCH_GATE,
    NEFF_GATE,
    OUTPUT_DIR as STAGE5_OUTPUT_DIR,
    PRESSURE_CUTOFF,
    RAW_GATE,
    SHRINKAGE_K,
)
from stage6_config import (  # noqa: E402
    COMPLETED_SCENARIOS,
    MANDATORY_SCENARIOS,
    OUTPUT_DIR,
    SCENARIOS,
    SCENARIO_BY_ID,
    SENSITIVITY_REFERENCE_MOMENTS,
)
from stage6_scoring import (  # noqa: E402
    add_delivery_metrics_param,
    compare_top10,
    compute_pressure_features_param,
    correlate_common,
    load_stage6_corpus,
    run_scenario,
    top10_ids,
)


def _pressure_frame() -> pd.DataFrame:
    """Three deliveries: one P1, one ordinary chase, one leverage trigger."""
    return pd.DataFrame(
        {
            "match_id": [1, 1, 1],
            "innings": [1, 2, 2],
            "match_format": ["T20", "T20", "T20"],
            "season": ["2023", "2023", "2023"],
            "legal_balls_before": [30.0, 90.0, 110.0],
            "max_balls": [120.0, 120.0, 120.0],
            "runs_before": [50.0, 120.0, 150.0],
            "wickets_before": [2.0, 6.0, 9.0],
            "runs_required": [np.nan, 60.0, 9.0],
            "target_provenance": [
                "",
                "STANDARD_TARGET",
                "STANDARD_TARGET",
            ],
            "is_target_reached_before": [False, False, False],
        }
    )


def _attribution_frame() -> pd.DataFrame:
    """Six deliveries covering legal, wide, other and overstep boundaries."""
    return pd.DataFrame(
        {
            "extras_type_clean": [
                "none", "wide", "other", "overstep", "none", "none", "other",
            ],
            "is_legal_delivery": [
                True, False, False, False, True, True, False,
            ],
            "is_dot_ball": [False] * 7,
            "is_four": [True, False, False, True, False, False, False],
            "is_six": [False] * 7,
            "batter_runs": [4, 0, 4, 4, 1, 6, 0],
            "extras_runs": [0, 1, 1, 1, 0, 0, 0],
            "is_wicket": [False] * 7,
            "dismissed_player_id": [None] * 7,
            "striker_id": [10] * 7,
            "dismissal_type_clean": [None] * 7,
            "is_bowler_wicket": [False] * 7,
            "season": ["2023"] * 7,
            "match_format": ["T20"] * 7,
            "w_bat": [1.0] * 7,
            "w_bowl": [1.0] * 7,
        }
    )


def _synthetic_players(ranks: list[int], z: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "player_id": list(range(1, len(ranks) + 1)),
            "ranking_eligible": True,
            "final_rank": ranks,
            "Z_comp": z,
        }
    )


class Stage6SensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load_stage6_corpus()
        cls.primary = run_scenario(
            cls.base, SCENARIO_BY_ID["PRIMARY"], keep_deliveries=True
        )
        cls.p65 = run_scenario(cls.base, SCENARIO_BY_ID["P_65"])
        cls.dismissal_b = run_scenario(
            cls.base, SCENARIO_BY_ID["DISMISSAL_RATE_WIDE_EXCLUDED"]
        )
        cls.boundary_proxy = run_scenario(
            cls.base, SCENARIO_BY_ID["BOUNDARY_RUNS_PROXY"]
        )
        cls.other_legal = run_scenario(
            cls.base, SCENARIO_BY_ID["OTHER_AS_LEGAL"], keep_deliveries=True
        )
        cls.season_equal = run_scenario(
            cls.base, SCENARIO_BY_ID["SEASON_EQUAL"], keep_deliveries=True
        )
        cls.fallback = run_scenario(
            cls.base, SCENARIO_BY_ID["MATCH_48610_P1_FALLBACK"]
        )
        cls.elig_m_all = run_scenario(cls.base, SCENARIO_BY_ID["ELIG_M_ALL"])
        cls.elig_per_format = run_scenario(
            cls.base, SCENARIO_BY_ID["ELIG_PER_FORMAT_M10"]
        )

    @classmethod
    def tearDownClass(cls):
        for name in (
            "base", "primary", "p65", "dismissal_b", "boundary_proxy",
            "other_legal", "season_equal", "fallback", "elig_m_all",
            "elig_per_format",
        ):
            if hasattr(cls, name):
                setattr(cls, name, None)

    # ------------------------------------------------------------------
    # Scenario registry
    # ------------------------------------------------------------------
    def test_01_scenario_registry(self):
        """The registry contains all approved, supplementary and blocked cases."""
        expected = {
            "PRIMARY", "P_55", "P_65", "K_25", "K_100", "NRAW_50", "NRAW_100",
            "WKT_RATE_NEFF_ALL_DELIVERIES", "DISMISSAL_RATE_WIDE_EXCLUDED",
            "BOUNDARY_RUNS_PROXY", "OTHER_BOUNDARY_LEGAL_OVERSTEP",
            "OTHER_BOUNDARY_LEGAL_ONLY", "OTHER_AS_LEGAL",
            "FORMAT_WEIGHT_NEFF_PROPORTIONAL", "CRR_FIRST_INNINGS",
            "ELIG_M_ALL", "ELIG_PER_FORMAT_M10", "NEFF_SCOPE_ALL_DELIVERIES",
            "MATCH_48610_P1_FALLBACK", "SEASON_EQUAL", "SEASON_2024_2026",
            "SUPP_SIGMA_8", "SUPP_SIGMA_10", "SUPP_SIGMA_15",
            "SUPP_SIGMA_20", "SUPP_H_LINEAR", "SUPP_H_QUADRATIC",
            "SUPP_LEVERAGE_0", "SUPP_LEVERAGE_1_5", "SUPP_LEVERAGE_5",
            "SUPP_WIDE_STUMP_REMOVED", "OPTIONAL_NEFF_CAPPED",
            "BASELINE_EXPOSURE_ALT",
        }
        self.assertEqual({s.scenario_id for s in SCENARIOS}, expected)
        self.assertEqual(len(SCENARIOS), 33)
        self.assertEqual(len(MANDATORY_SCENARIOS), 21)
        self.assertEqual(len(COMPLETED_SCENARIOS), 31)
        self.assertEqual(
            len([s for s in SCENARIOS if s.status == "COMPLETED_SUPPLEMENTARY"]),
            10,
        )
        blocked = [
            s
            for s in SCENARIOS
            if s.status in {"BLOCKED_NOT_APPROVED", "OPTIONAL_NOT_RUN"}
        ]
        self.assertEqual(
            {s.scenario_id for s in blocked},
            {"OPTIONAL_NEFF_CAPPED", "BASELINE_EXPOSURE_ALT"},
        )
        self.assertTrue(all(s.blocked_reason for s in blocked))
        self.assertTrue(
            all(s.status.startswith("BLOCKED") or s.status == "OPTIONAL_NOT_RUN" for s in blocked)
        )

        primary = SCENARIO_BY_ID["PRIMARY"]
        self.assertEqual(primary.pressure_cutoff, PRESSURE_CUTOFF)
        self.assertEqual(primary.shrinkage_k, SHRINKAGE_K)
        self.assertEqual(primary.raw_gate, RAW_GATE)
        self.assertEqual(primary.neff_gate, NEFF_GATE)
        self.assertEqual(primary.match_gate, MATCH_GATE)
        self.assertEqual(primary.sigma, 12.0)
        self.assertEqual(primary.leverage, 3.0)
        self.assertEqual(primary.h_mode, "sqrt")
        self.assertEqual(primary.cross_format_weight, "equal")
        self.assertFalse(primary.other_as_legal)
        self.assertFalse(primary.include_48610_chase)

    # ------------------------------------------------------------------
    # Primary reproduction
    # ------------------------------------------------------------------
    def test_02_primary_reproduces_stage5(self):
        """The parameterized engine reproduces Stage 5 scores, ranks and top 10."""
        expected_counts = {"batter": 101, "bowler": 141}
        expected_top = {
            "batter": [3374, 4369, 6288, 37052, 2485, 2930, 1699, 2921, 4246, 6651],
            "bowler": [4658, 4840, 7364, 7690, 781, 7699, 1596, 7503, 6643, 8661],
        }
        for role in ("batter", "bowler"):
            got = self.primary[f"{role}_players"]
            exp = pd.read_csv(STAGE5_OUTPUT_DIR / f"{role}_scoring.csv")
            self.assertEqual(int(got["ranking_eligible"].sum()), expected_counts[role])
            self.assertEqual(
                set(got.loc[got["ranking_eligible"], "player_id"]),
                set(exp.loc[exp["ranking_eligible"], "player_id"]),
            )
            merged = got.merge(exp, on="player_id", suffixes=("_g", "_e"))
            eligible = merged[merged["ranking_eligible_g"].astype(bool)]
            np.testing.assert_array_equal(
                eligible["final_rank_g"].astype(int).to_numpy(),
                eligible["final_rank_e"].astype(int).to_numpy(),
            )
            self.assertLess(
                float((eligible["Z_comp_g"] - eligible["Z_comp_e"]).abs().max()),
                1e-8,
            )
            self.assertEqual(top10_ids(got), expected_top[role])

        diag = self.primary["diagnostics"]
        self.assertEqual(diag["corpus_rows"], 191_963)
        self.assertEqual(diag["matches"], 812)
        self.assertEqual(diag["boundary_count_all"], 9_816)

    def test_03_pressure_cutoff_comparison(self):
        """P=65 reproduces the registered eligible counts and stability metrics."""
        self.assertEqual(int(self.p65["batter_players"]["ranking_eligible"].sum()), 93)
        self.assertEqual(int(self.p65["bowler_players"]["ranking_eligible"].sum()), 133)
        self.assertEqual(self.p65["diagnostics"]["boundary_count_all"], 9_031)

        for role, overlap, rho in (
            ("batter", 7, 0.9357),
            ("bowler", 6, 0.9722),
        ):
            metrics = correlate_common(
                self.primary[f"{role}_players"], self.p65[f"{role}_players"]
            )
            top = compare_top10(
                self.primary[f"{role}_players"], self.p65[f"{role}_players"]
            )
            self.assertEqual(top["top10_overlap"], overlap)
            self.assertAlmostEqual(metrics["spearman_rank"], rho, places=4)
            self.assertGreater(metrics["kendall_rank"], 0.75)
            self.assertGreater(metrics["common_n"], 80)

    # ------------------------------------------------------------------
    # Parameterized pressure engine
    # ------------------------------------------------------------------
    def test_04_sigma_h_and_leverage_only_change_chase_rows(self):
        """Sigma, h and leverage affect P2 but never the P1 first innings rows."""
        frame = _pressure_frame()
        base = SCENARIO_BY_ID["PRIMARY"]
        p1 = compute_pressure_features_param(frame, base)

        sigma8 = compute_pressure_features_param(
            frame, dataclasses.replace(base, sigma=8.0)
        )
        sigma20 = compute_pressure_features_param(
            frame, dataclasses.replace(base, sigma=20.0)
        )
        self.assertAlmostEqual(
            float(sigma8.loc[0, "p_bowl"]), float(sigma20.loc[0, "p_bowl"]), places=12
        )
        self.assertEqual(float(sigma8.loc[0, "p_bowl"]), float(p1.loc[0, "p_bowl"]))
        self.assertGreater(
            abs(float(sigma8.loc[1, "p_bowl"]) - float(sigma20.loc[1, "p_bowl"])),
            0.05,
        )
        # Sigma changes P_bowl only; P_bat is a demand expression.
        np.testing.assert_allclose(sigma8["p_bat"], sigma20["p_bat"], rtol=1e-12)

        linear = compute_pressure_features_param(
            frame, dataclasses.replace(base, h_mode="linear")
        )
        quadratic = compute_pressure_features_param(
            frame, dataclasses.replace(base, h_mode="quadratic")
        )
        self.assertAlmostEqual(
            float(linear.loc[0, "p_bowl"]), float(quadratic.loc[0, "p_bowl"]), places=12
        )
        self.assertGreater(
            abs(float(linear.loc[1, "p_bowl"]) - float(quadratic.loc[1, "p_bowl"])),
            0.01,
        )

        lev0 = compute_pressure_features_param(
            frame, dataclasses.replace(base, leverage=0.0)
        )
        lev5 = compute_pressure_features_param(
            frame, dataclasses.replace(base, leverage=5.0)
        )
        # The trigger is row 2 only.
        self.assertAlmostEqual(
            float(lev0.loc[0, "p_bowl"]), float(lev5.loc[0, "p_bowl"]), places=12
        )
        self.assertAlmostEqual(
            float(lev0.loc[1, "p_bowl"]), float(lev5.loc[1, "p_bowl"]), places=12
        )
        self.assertGreater(
            abs(float(lev0.loc[2, "p_bowl"]) - float(lev5.loc[2, "p_bowl"])),
            1.0,
        )

    def test_05_pressure_threshold_and_unresolved_rows(self):
        """Weights are zero below the cutoff and unresolved chases are excluded."""
        frame = _pressure_frame()
        out = compute_pressure_features_param(frame, SCENARIO_BY_ID["PRIMARY"])
        for p_col, w_col in (("p_bat", "w_bat"), ("p_bowl", "w_bowl")):
            below = out[out[p_col] < PRESSURE_CUTOFF]
            self.assertTrue((below[w_col] == 0).all())
            above = out[out[p_col] >= PRESSURE_CUTOFF]
            np.testing.assert_allclose(
                above[w_col].to_numpy(),
                np.square(above[p_col].to_numpy() / 100.0),
                rtol=1e-12,
            )

        unresolved = frame.copy()
        unresolved.loc[2, "target_provenance"] = ""
        out = compute_pressure_features_param(
            unresolved, SCENARIO_BY_ID["PRIMARY"]
        )
        self.assertTrue(np.isnan(out.loc[2, "p_bat"]))
        self.assertTrue(np.isnan(out.loc[2, "p_bowl"]))
        fallback = compute_pressure_features_param(
            unresolved, SCENARIO_BY_ID["PRIMARY"], unresolved_fallback=True
        )
        self.assertTrue(np.isfinite(fallback.loc[2, "p_bat"]))
        self.assertEqual(fallback.loc[2, "pressure_basis"], "P1_FALLBACK_SENSITIVITY")

    # ------------------------------------------------------------------
    # Delivery attribution variants
    # ------------------------------------------------------------------
    def test_06_other_as_legal_treatment(self):
        """`other` becomes legal, dot-coded by runs, and keeps bowler charges."""
        diag = self.other_legal["diagnostics"]
        self.assertEqual(diag["other_rows"], 256)
        self.assertEqual(diag["other_legal_rows"], 256)
        self.assertEqual(diag["boundary_count_all"], 9_816)

        frame = _attribution_frame()
        out = add_delivery_metrics_param(frame, SCENARIO_BY_ID["OTHER_AS_LEGAL"])
        other = out["extras_type_clean"] == "other"
        self.assertTrue((out.loc[other, "legal"] == 1).all())
        expected_dot = (
            (out.loc[other, "batter_runs"] + out.loc[other, "extras_runs"]) == 0
        ).astype(float)
        np.testing.assert_array_equal(out.loc[other, "dot_i"].to_numpy(), expected_dot.to_numpy())
        # Bowler runs on `other` remain batter runs plus extras.
        self.assertEqual(
            float(out.loc[2, "bowler_runs"]), float(frame.loc[2, "batter_runs"] + frame.loc[2, "extras_runs"])
        )
        self.assertEqual(
            float(out.loc[6, "bowler_runs"]), 0.0
        )

    def test_07_boundary_legality_and_source(self):
        """Boundary counts and the runs proxy follow the approved rules."""
        diag = self.primary["diagnostics"]
        self.assertEqual(
            (
                diag["boundary_count_all"],
                diag["boundary_count_legal_overstep"],
                diag["boundary_count_legal_only"],
            ),
            (9_816, 9_790, 9_756),
        )

        pressure = self.primary["deliveries"]
        pressure = pressure[pressure["p_bowl"] >= PRESSURE_CUTOFF]
        boundary = pressure["boundary_bowler"].astype(bool)
        legal = pressure["legal"].astype(bool)
        overstep = pressure["extras_type_clean"].eq("overstep")
        self.assertEqual(int(boundary.sum()), 9_816)
        self.assertEqual(int((boundary & (legal | overstep)).sum()), 9_790)
        self.assertEqual(int((boundary & legal).sum()), 9_756)

        frame = _attribution_frame()
        flags = add_delivery_metrics_param(frame, SCENARIO_BY_ID["PRIMARY"])
        proxy = add_delivery_metrics_param(
            frame, SCENARIO_BY_ID["BOUNDARY_RUNS_PROXY"]
        )
        expected_flags = pd.Series([1, 0, 0, 1, 0, 0, 0], dtype=float)
        expected_proxy = pd.Series([1, 0, 1, 1, 0, 1, 0], dtype=float)
        np.testing.assert_array_equal(flags["boundary_batter"], expected_flags)
        np.testing.assert_array_equal(proxy["boundary_batter"], expected_proxy)
        # The runs proxy is a batter-only sensitivity.  Bowler boundary-conceded
        # keeps the source flags, so the overstep four remains counted.
        np.testing.assert_array_equal(
            proxy["boundary_bowler"], pd.Series([1, 0, 0, 1, 0, 0, 0], dtype=float)
        )

        legal_overstep = add_delivery_metrics_param(
            frame, SCENARIO_BY_ID["OTHER_BOUNDARY_LEGAL_OVERSTEP"]
        )
        legal_only = add_delivery_metrics_param(
            frame, SCENARIO_BY_ID["OTHER_BOUNDARY_LEGAL_ONLY"]
        )
        np.testing.assert_array_equal(
            legal_overstep["boundary_bowler"], pd.Series([1, 0, 0, 1, 0, 0, 0], dtype=float)
        )
        np.testing.assert_array_equal(
            legal_only["boundary_bowler"], pd.Series([1, 0, 0, 0, 0, 0, 0], dtype=float)
        )

    def test_07b_approved_alternative_moments_and_role_scope(self):
        """Published B/proxy moments are used and bowler scores stay primary."""
        for scenario_id, result in (
            ("DISMISSAL_RATE_WIDE_EXCLUDED", self.dismissal_b),
            ("BOUNDARY_RUNS_PROXY", self.boundary_proxy),
        ):
            records = result["batter_records"]
            for (_role, fmt, metric), (mean, sd) in SENSITIVITY_REFERENCE_MOMENTS[
                scenario_id
            ].items():
                subset = records[records["match_format"] == fmt]
                expected = (
                    subset[f"shrunk_{metric}"].astype(float) - mean
                ) / sd
                np.testing.assert_allclose(
                    subset[f"z_{metric}"].astype(float),
                    expected,
                    rtol=1e-12,
                    atol=1e-12,
                )

            got = result["bowler_players"]
            exp = self.primary["bowler_players"]
            self.assertEqual(
                set(got.loc[got["ranking_eligible"], "player_id"]),
                set(exp.loc[exp["ranking_eligible"], "player_id"]),
            )
            merged = got.merge(exp, on="player_id", suffixes=("_g", "_e"))
            both = merged[
                merged["ranking_eligible_g"].astype(bool)
                & merged["ranking_eligible_e"].astype(bool)
            ]
            np.testing.assert_array_equal(
                both["final_rank_g"].astype(int).to_numpy(),
                both["final_rank_e"].astype(int).to_numpy(),
            )
            self.assertLess(
                float((both["Z_comp_g"] - both["Z_comp_e"]).abs().max()),
                1e-12,
            )

    def test_07c_definition_b_keeps_the_primary_baseline(self):
        """Definition B changes the pressure numerator only, not the baseline."""
        primary = self.primary["batter_records"]
        definition_b = self.dismissal_b["batter_records"]
        merged = primary.merge(
            definition_b,
            on=["match_format", "player_id"],
            suffixes=("_p", "_b"),
        )
        np.testing.assert_allclose(
            merged["DR_base_b"].astype(float),
            merged["DR_base_p"].astype(float),
            rtol=1e-12,
            atol=1e-12,
        )
        expected = merged["DR_base_p"].astype(float) - merged["DR_P_b"].astype(float)
        expected_shrunk = (
            merged["N_eff_BF_b"].astype(float)
            / (merged["N_eff_BF_b"].astype(float) + 50.0)
        ) * expected
        np.testing.assert_allclose(
            merged["shrunk_dDR_b"].astype(float),
            expected_shrunk,
            rtol=1e-12,
            atol=1e-12,
        )

        for (_role, fmt, metric), (mean, sd) in SENSITIVITY_REFERENCE_MOMENTS[
            "DISMISSAL_RATE_WIDE_EXCLUDED"
        ].items():
            subset = definition_b[definition_b["match_format"] == fmt].copy()
            subset = subset[
                (subset["N_raw"] >= 75)
                & (subset["N_eff_del"] >= 35)
                & (subset["sum_wbf"] > 0)
                & subset["baseline_ok"].astype(bool)
                & np.isfinite(subset[f"shrunk_{metric}"])
            ]
            self.assertAlmostEqual(
                float(subset[f"shrunk_{metric}"].mean()), mean, places=6
            )
            self.assertAlmostEqual(
                float(subset[f"shrunk_{metric}"].std(ddof=0)), sd, places=6
            )

    def test_08_season_equal_weights(self):
        """Every format-season with pressure weight contributes total weight one."""
        deliveries = self.season_equal["deliveries"]
        grouped = deliveries.groupby(["match_format", "season"])[["w_bat", "w_bowl"]].sum()
        for col in ("w_bat", "w_bowl"):
            totals = grouped[col][grouped[col] > 0]
            self.assertGreater(len(totals), 0)
            np.testing.assert_allclose(totals.to_numpy(), 1.0, rtol=1e-12, atol=1e-12)
        self.assertEqual(
            int(self.season_equal["batter_players"]["ranking_eligible"].sum()), 98
        )
        self.assertEqual(
            int(self.season_equal["bowler_players"]["ranking_eligible"].sum()), 131
        )

    # ------------------------------------------------------------------
    # Eligibility gates and Match 48610 fallback
    # ------------------------------------------------------------------
    def test_09_eligibility_alternatives(self):
        """M_all and per-format M>=10 gates are applied exactly as declared."""
        primary = self.primary
        for role in ("batter", "bowler"):
            elig = primary[f"{role}_players"]
            elig = elig[elig["ranking_eligible"]]
            self.assertTrue((elig["M_role"].astype(int) >= MATCH_GATE).all())
            ready = primary[f"{role}_records"]
            ready = ready[ready["composite_ready"]]
            self.assertTrue((ready["N_raw"] >= RAW_GATE).all())
            self.assertTrue((ready["N_eff_del"] >= NEFF_GATE).all())
            self.assertTrue(ready["baseline_ok"].astype(bool).all())

        m_all_counts = {"batter": 103, "bowler": 146}
        for role in ("batter", "bowler"):
            elig = self.elig_m_all[f"{role}_players"]
            elig = elig[elig["ranking_eligible"]]
            self.assertEqual(len(elig), m_all_counts[role])
            self.assertTrue((elig["M_all"].astype(int) >= MATCH_GATE).all())

        per_format_counts = {"batter": 101, "bowler": 139}
        for role in ("batter", "bowler"):
            result = self.elig_per_format
            elig = result[f"{role}_players"]
            elig = elig[elig["ranking_eligible"]]
            self.assertEqual(len(elig), per_format_counts[role])
            self.assertTrue((elig["M_role"].astype(int) >= MATCH_GATE).all())
            ready = result[f"{role}_records"]
            ready = ready[ready["composite_ready"]]
            self.assertTrue((ready["M_format"].astype(int) >= MATCH_GATE).all())

    def test_10_match_48610_p1_fallback(self):
        """The fallback includes the 93 chase rows and reproduces boundary counts."""
        diag = self.fallback["diagnostics"]
        self.assertEqual(diag["corpus_rows"], 192_056)
        self.assertEqual(
            (
                diag["boundary_count_all"],
                diag["boundary_count_legal_overstep"],
                diag["boundary_count_legal_only"],
            ),
            (9_827, 9_801, 9_767),
        )
        for role in ("batter", "bowler"):
            top = compare_top10(
                self.primary[f"{role}_players"], self.fallback[f"{role}_players"]
            )
            self.assertEqual(top["top10_overlap"], 10)
            metrics = correlate_common(
                self.primary[f"{role}_players"], self.fallback[f"{role}_players"]
            )
            self.assertGreater(metrics["spearman_rank"], 0.99)

    # ------------------------------------------------------------------
    # Stability helper mathematics
    # ------------------------------------------------------------------
    def test_11_top10_overlap_and_correlation_helpers(self):
        """Overlap, Jaccard, entrants/leavers and correlations are exact."""
        ranks = list(range(1, 16))
        z = [float(16 - rank) for rank in ranks]
        primary = _synthetic_players(ranks, z)

        same = compare_top10(primary, primary)
        self.assertEqual(same["top10_overlap"], 10)
        self.assertEqual(same["top10_jaccard"], 1.0)
        self.assertEqual(same["entrants"], [])
        self.assertEqual(same["leavers"], [])
        identical = correlate_common(primary, primary)
        self.assertEqual(identical["common_n"], 15)
        self.assertAlmostEqual(identical["spearman_rank"], 1.0, places=12)
        self.assertAlmostEqual(identical["kendall_rank"], 1.0, places=12)

        swapped = primary.copy()
        swapped.loc[swapped["player_id"] == 10, "final_rank"] = 11
        swapped.loc[swapped["player_id"] == 11, "final_rank"] = 10
        moved = compare_top10(primary, swapped)
        self.assertEqual(moved["top10_overlap"], 9)
        self.assertAlmostEqual(moved["top10_jaccard"], 9 / 11)
        self.assertEqual(moved["entrants"], [11])
        self.assertEqual(moved["leavers"], [10])

        reversed_frame = primary.copy()
        reversed_frame["final_rank"] = list(range(15, 0, -1))
        reversed_frame["Z_comp"] = list(range(1, 16))
        reverse = correlate_common(primary, reversed_frame)
        self.assertAlmostEqual(reverse["spearman_rank"], -1.0, places=12)
        self.assertAlmostEqual(reverse["kendall_rank"], -1.0, places=12)

    # ------------------------------------------------------------------
    # Generated Stage 6 deliverables
    # ------------------------------------------------------------------
    def test_12_generated_outputs_and_report(self):
        """The Stage 6 CSVs and report are complete and pass their own checks."""
        summary_path = OUTPUT_DIR / "sensitivity_summary.csv"
        checks_path = OUTPUT_DIR / "stage6_validation_checks.csv"
        report_path = PROJECT_ROOT / "reports" / "stage6_sensitivity_report.md"
        if not (summary_path.exists() and checks_path.exists() and report_path.exists()):
            self.skipTest("Stage 6 outputs have not been generated yet")

        summary = pd.read_csv(summary_path)
        self.assertEqual(len(summary), 33)
        self.assertEqual(set(summary["scenario_id"]), {s.scenario_id for s in SCENARIOS})
        mandatory = summary[summary["mandatory"].astype(bool)]
        self.assertTrue(
            mandatory["status"].isin(["PRIMARY", "COMPLETED"]).all()
        )
        blocked = summary[summary["scenario_id"].isin(
            ["OPTIONAL_NEFF_CAPPED", "BASELINE_EXPOSURE_ALT"]
        )]
        self.assertTrue(
            blocked["status"].isin(["OPTIONAL_NOT_RUN", "BLOCKED_NOT_APPROVED"]).all()
        )

        checks = pd.read_csv(checks_path)
        self.assertGreaterEqual(len(checks), 20)
        self.assertTrue(checks["passed"].astype(bool).all())

        text = report_path.read_text(encoding="utf-8")
        self.assertIn("Stage 6", text)
        self.assertIn("Most stable primary top-10 batters", text)
        self.assertIn("Most sensitive primary top-10 bowlers", text)
        self.assertRegex(text, re.compile(r"changes by at most four members"))
        self.assertRegex(
            text, re.compile(r"Individual rank movements can be substantially larger")
        )


if __name__ == "__main__":
    unittest.main()
