"""
Stage 5 primary scoring tests.

These tests exercise the approved Stage 4.2 pressure equations, delivery
attribution, format-level aggregation, eligibility gates, calibration,
reliability and deterministic ranking.  The final test runs the independent
validation layer to guard against a test suite that only rechecks the engine
against itself.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stage5_config import (  # noqa: E402
    BATTER_METRICS,
    BOWLER_METRICS,
    CALIBRATION,
    FORMAT_ORDER,
    MATCH_GATE,
    NEFF_GATE,
    PRESSURE_CUTOFF,
    RAW_GATE,
    REFERENCE_MOMENTS,
    RELIABILITY_GAMMA,
    SHRINKAGE_K,
    MU_PEER,
)
from stage5_scoring import (  # noqa: E402
    add_delivery_metrics,
    build_stage5_tables,
    compute_pressure_features,
)
from stage5_validation import run_validation_checks  # noqa: E402


class TestStage5Scoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Build the scoring tables once for the whole test class."""
        cls.result = build_stage5_tables()
        cls.audit = cls.result["audit"]
        cls.scoring = cls.result["scoring"]
        cls.batter_records = cls.result["batter_records"]
        cls.bowler_records = cls.result["bowler_records"]
        cls.batter_players = cls.result["batter_players"]
        cls.bowler_players = cls.result["bowler_players"]
        cls.top_batters = cls.result["top10_batters"]
        cls.top_bowlers = cls.result["top10_bowlers"]

    # ------------------------------------------------------------------
    # Method locks and pressure equations
    # ------------------------------------------------------------------
    def test_01_locked_methodology_constants(self):
        """The approved thresholds, weights and calibration values are locked."""
        self.assertEqual(PRESSURE_CUTOFF, 60.0)
        self.assertEqual(RAW_GATE, 75)
        self.assertEqual(NEFF_GATE, 35.0)
        self.assertEqual(MATCH_GATE, 10)
        self.assertEqual(SHRINKAGE_K, 50.0)
        self.assertEqual(RELIABILITY_GAMMA, 0.80)
        self.assertAlmostEqual(sum(w for _, w, *_ in BATTER_METRICS), 1.0)
        self.assertAlmostEqual(sum(w for _, w, *_ in BOWLER_METRICS), 1.0)
        self.assertAlmostEqual(CALIBRATION["batter"]["mu"], 0.1036068081)
        self.assertAlmostEqual(CALIBRATION["batter"]["sigma"], 0.6610638828)
        self.assertAlmostEqual(CALIBRATION["batter"]["n"], 122)
        self.assertAlmostEqual(CALIBRATION["bowler"]["mu"], 0.0256919707)
        self.assertAlmostEqual(CALIBRATION["bowler"]["sigma"], 0.6655792246)
        self.assertAlmostEqual(CALIBRATION["bowler"]["n"], 173)

    def test_02_pressure_worked_examples_and_canonical_scenarios(self):
        """P1 worked examples and all eight P2 canonical scenarios reproduce."""
        rows = [
            # name, innings, b, max_balls, runs_before, wickets, runs_req, p_bat, p_bowl
            ("P1-ex1", 1, 56, 72, 82, 3, np.nan, 65.2, 46.7),
            ("P1-ex2", 1, 27, 120, 22, 4, np.nan, 73.9, 6.1),
            ("S1", 2, 96, 120, 0, 2, 48, 75.3, 23.0),
            ("S2", 2, 96, 120, 0, 8, 48, 94.0, 1.8),
            ("S3", 2, 114, 120, 0, 9, 6, 86.4, 98.1),
            ("S4", 2, 90, 120, 0, 0, 24, 17.5, 4.3),
            ("S5", 2, 114, 120, 0, 4, 42, 99.2, 1.6),
            ("S6", 2, 117, 120, 0, 8, 4, 88.0, 79.3),
            ("S7", 2, 102, 120, 0, 5, 30, 79.2, 49.3),
            ("S8", 2, 30, 60, 0, 2, 45, 48.5, 83.0),
        ]
        frame = pd.DataFrame(
            [
                {
                    "scenario": name,
                    "innings": innings,
                    "legal_balls_before": b,
                    "max_balls": mb,
                    "runs_before": runs_before,
                    "wickets_before": wickets,
                    "runs_required": runs_req,
                    "match_format": "T20",
                    "target_provenance": (
                        "NOT_APPLICABLE" if innings == 1 else "STANDARD_TARGET"
                    ),
                    "is_target_reached_before": False,
                }
                for name, innings, b, mb, runs_before, wickets, runs_req, _, _ in rows
            ]
        )
        out = compute_pressure_features(frame)
        for idx, row in enumerate(rows):
            name, _, _, _, _, _, _, expected_bat, expected_bowl = row
            self.assertAlmostEqual(
                out.loc[idx, "p_bat"], expected_bat, delta=0.1, msg=name
            )
            self.assertAlmostEqual(
                out.loc[idx, "p_bowl"], expected_bowl, delta=0.1, msg=name
            )

    def test_03_other_extras_and_delivery_attribution(self):
        """`other` is provisional no-ball-like; attribution follows the rule."""
        frame = pd.DataFrame(
            {
                "extras_type_clean": ["none", "wide", "other", "none", "none"],
                "is_legal_delivery": [True, False, False, True, True],
                "is_dot_ball": [False, False, False, False, True],
                "is_four": [True, False, True, False, False],
                "is_six": [False, False, False, False, False],
                "is_wicket": [False, False, False, True, True],
                "dismissed_player_id": [None, None, None, 99, 10],
                "striker_id": [10, 10, 10, 10, 10],
                "dismissal_type_clean": [None, None, None, "Run Out", "Retire Out"],
                "batter_runs": [4, 0, 4, 0, 0],
                "extras_runs": [0, 1, 1, 0, 0],
            }
        )
        out = add_delivery_metrics(frame)
        self.assertEqual(out.loc[0, "BF"], 1)
        self.assertEqual(out.loc[1, "BF"], 0)  # wide is not a ball faced
        self.assertEqual(out.loc[2, "BF"], 1)  # other is a ball faced
        self.assertEqual(out.loc[2, "legal"], 0)
        self.assertEqual(out.loc[2, "boundary"], 1)
        self.assertEqual(out.loc[2, "bowler_runs"], 5)  # batter 4 + extras 1
        self.assertEqual(out.loc[1, "bowler_runs"], 1)  # wide: 0 + 1
        self.assertEqual(out.loc[3, "D"], 0)  # non-striker run-out
        self.assertEqual(out.loc[4, "D"], 0)  # Retire Out excluded
        self.assertEqual(out.loc[0, "D"], 0)

    # ------------------------------------------------------------------
    # Corpus, Match 48610 and Q10 boundary reconciliation
    # ------------------------------------------------------------------
    def test_04_corpus_and_match_48610_rules(self):
        """The scoring and audit corpora reconcile exactly."""
        self.assertEqual(len(self.audit), 192_056)
        self.assertEqual(len(self.scoring), 191_963)
        self.assertEqual(self.scoring["match_id"].nunique(), 812)
        self.assertEqual(
            int((self.scoring["match_format"] == "T20").sum()), 87_217
        )
        self.assertEqual(
            int((self.scoring["match_format"] == "T20I").sum()), 104_746
        )
        m48610 = self.audit[self.audit["match_id"] == 48610]
        self.assertEqual(len(m48610[m48610["innings"] == 1]), 101)
        self.assertEqual(len(m48610[m48610["innings"] == 2]), 93)
        self.assertEqual(
            len(self.scoring[self.scoring["match_id"] == 48610]), 101
        )
        self.assertFalse(
            (
                (self.scoring["match_id"] == 48610)
                & (self.scoring["innings"] == 2)
            ).any()
        )
        self.assertEqual(
            int((self.audit["extras_type_clean"] == "other").sum()), 256
        )
        self.assertEqual(
            int((self.scoring["extras_type_clean"] == "other").sum()), 256
        )

    def test_05_q10_boundary_counts_and_weighted_numerators(self):
        """Audit and scoring boundary treatments reproduce the approved counts."""
        expected = {
            "audit": {
                "counts": {"legal": 9_767, "overstep": 9_801, "all": 9_827},
                "weighted": {
                    "legal": 6_552.537349,
                    "overstep": 6_576.615108,
                    "all": 6_594.333604,
                },
                "denominator": 30_057.770551,
            },
            "scoring": {
                "counts": {"legal": 9_756, "overstep": 9_790, "all": 9_816},
                "weighted": {
                    "legal": 6_547.268516,
                    "overstep": 6_571.346275,
                    "all": 6_589.064771,
                },
                "denominator": 30_021.669303,
            },
        }
        for label, frame in (("audit", self.audit), ("scoring", self.scoring)):
            pressure = frame[frame["p_bowl"] >= PRESSURE_CUTOFF]
            boundary = pressure["boundary"].astype(bool)
            legal = pressure["legal"].astype(bool)
            overstep = pressure["extras_type_clean"].eq("overstep")
            counts = {
                "legal": int((boundary & legal).sum()),
                "overstep": int((boundary & (legal | overstep)).sum()),
                "all": int(boundary.sum()),
            }
            self.assertEqual(counts, expected[label]["counts"])
            weighted = {
                "legal": float(pressure.loc[boundary & legal, "w_bowl"].sum()),
                "overstep": float(
                    pressure.loc[boundary & (legal | overstep), "w_bowl"].sum()
                ),
                "all": float(pressure.loc[boundary, "w_bowl"].sum()),
            }
            for key in weighted:
                self.assertAlmostEqual(
                    weighted[key], expected[label]["weighted"][key], places=5
                )
            self.assertAlmostEqual(
                float(pressure.loc[legal, "w_bowl"].sum()),
                expected[label]["denominator"],
                places=5,
            )

    # ------------------------------------------------------------------
    # Format-level aggregation
    # ------------------------------------------------------------------
    def test_06_batter_format_record_formulas(self):
        """Batter N_eff, metrics, baselines and gates follow the approved rules."""
        r = self.batter_records
        np.testing.assert_allclose(
            r["N_eff_del"], np.square(r["sum_w"]) / r["sum_w2"], rtol=1e-12
        )
        np.testing.assert_allclose(
            r["N_eff_BF"],
            np.square(r["sum_wbf"]) / r["sum_wbf2"].replace(0, np.nan),
            rtol=1e-12,
        )
        np.testing.assert_allclose(
            r["N_eff_legal"],
            np.square(r["sum_wlegal"]) / r["sum_wlegal2"].replace(0, np.nan),
            rtol=1e-12,
        )
        np.testing.assert_allclose(
            r["SR_P"], 100.0 * r["sum_wr"] / r["sum_wbf"].replace(0, np.nan)
        )
        np.testing.assert_allclose(
            r["Boundary_P"],
            100.0 * r["sum_wbound"] / r["sum_wbf"].replace(0, np.nan),
        )
        np.testing.assert_allclose(
            r["Dot_P"],
            100.0 * r["sum_wdot"] / r["sum_wlegal"].replace(0, np.nan),
        )
        np.testing.assert_allclose(
            r["DR_P"], 100.0 * r["sum_wD"] / r["sum_wbf"].replace(0, np.nan)
        )
        expected_baseline = (r["baseline_BF"].fillna(0) >= 120) & (
            r["baseline_legal"].fillna(0) >= 120
        )
        self.assertTrue(
            np.array_equal(r["baseline_ok"].astype(bool), expected_baseline)
        )
        expected_gate = (r["N_raw"] >= RAW_GATE) & (
            r["N_eff_del"] >= NEFF_GATE
        )
        self.assertTrue(
            np.array_equal(r["format_gate"].astype(bool), expected_gate)
        )
        expected_ready = (
            expected_gate
            & expected_baseline
            & r["denoms_ok"].astype(bool)
            & np.isfinite(r["Z_comp_format"])
        )
        self.assertTrue(
            np.array_equal(r["composite_ready"].astype(bool), expected_ready)
        )

    def test_07_bowler_format_record_formulas(self):
        """Bowler N_eff, metrics, baselines and gates follow the approved rules."""
        r = self.bowler_records
        np.testing.assert_allclose(
            r["N_eff_del"], np.square(r["sum_w"]) / r["sum_w2"], rtol=1e-12
        )
        np.testing.assert_allclose(
            r["N_eff_legal"],
            np.square(r["sum_wlegal"]) / r["sum_wlegal2"].replace(0, np.nan),
            rtol=1e-12,
        )
        np.testing.assert_allclose(
            r["Econ_P"], 6.0 * r["sum_wr"] / r["sum_wlegal"].replace(0, np.nan)
        )
        np.testing.assert_allclose(
            r["WktRate_P"],
            r["sum_wwkt"] / r["sum_wlegal"].replace(0, np.nan),
        )
        np.testing.assert_allclose(
            r["Dot_bowl_P"],
            100.0 * r["sum_wdot"] / r["sum_wlegal"].replace(0, np.nan),
        )
        np.testing.assert_allclose(
            r["BoundaryConc_P"],
            100.0 * r["sum_wbound"] / r["sum_wlegal"].replace(0, np.nan),
        )
        expected_baseline = r["baseline_legal"].fillna(0) >= 120
        self.assertTrue(
            np.array_equal(r["baseline_ok"].astype(bool), expected_baseline)
        )
        expected_gate = (r["N_raw"] >= RAW_GATE) & (
            r["N_eff_del"] >= NEFF_GATE
        )
        self.assertTrue(
            np.array_equal(r["format_gate"].astype(bool), expected_gate)
        )
        expected_ready = (
            expected_gate
            & expected_baseline
            & r["denoms_ok"].astype(bool)
            & np.isfinite(r["Z_comp_format"])
        )
        self.assertTrue(
            np.array_equal(r["composite_ready"].astype(bool), expected_ready)
        )

    def test_08_shrinkage_z_scores_and_weighted_composite(self):
        """K=50 shrinkage, approved moments and 30/25/20/15/10 weights."""
        for role, records, metrics in (
            ("batter", self.batter_records, BATTER_METRICS),
            ("bowler", self.bowler_records, BOWLER_METRICS),
        ):
            for name, weight, raw_col, neff_col, use_peer, sign in metrics:
                neff = records[neff_col].astype(float)
                raw = records[raw_col].astype(float)
                prior = (
                    records["match_format"].map(lambda f: MU_PEER[(f, name)])
                    if use_peer
                    else 0.0
                )
                expected_shrunk = (neff / (neff + SHRINKAGE_K)) * raw + (
                    SHRINKAGE_K / (neff + SHRINKAGE_K)
                ) * prior
                np.testing.assert_allclose(
                    records[f"shrunk_{name}"],
                    expected_shrunk,
                    rtol=1e-12,
                    atol=1e-12,
                )
                mean_sd = records["match_format"].map(
                    lambda f: REFERENCE_MOMENTS[(role, f, name)]
                )
                expected_z = (
                    expected_shrunk - mean_sd.map(lambda x: x[0])
                ) / mean_sd.map(lambda x: x[1])
                np.testing.assert_allclose(
                    records[f"z_{name}"], expected_z, rtol=1e-12, atol=1e-12
                )
            expected_composite = sum(
                sign * weight * records[f"z_{name}"]
                for name, weight, _, _, _, sign in metrics
            )
            np.testing.assert_allclose(
                records["Z_comp_format"],
                expected_composite,
                rtol=1e-12,
                atol=1e-12,
            )

    # ------------------------------------------------------------------
    # Eligibility, calibration and reliability
    # ------------------------------------------------------------------
    def test_09_eligibility_populations(self):
        """Approved record/player populations and the final M_role gate."""
        expected = {
            "batter": (144, 122, 123, 101, 21, 122),
            "bowler": (209, 173, 177, 141, 32, 173),
        }
        for role, records, players in (
            ("batter", self.batter_records, self.batter_players),
            ("bowler", self.bowler_records, self.bowler_players),
        ):
            (
                f_records,
                f_players,
                final_records,
                final_players,
                m_lt_10,
                calibration,
            ) = expected[role]
            self.assertEqual(int(records["composite_ready"].sum()), f_records)
            self.assertEqual(
                int(
                    records.loc[
                        records["composite_ready"], "player_id"
                    ].nunique()
                ),
                f_players,
            )
            self.assertEqual(int(records["ranking_eligible"].sum()), final_records)
            self.assertEqual(int(players["ranking_eligible"].sum()), final_players)
            self.assertEqual(
                int((players["status"] == "M_BREADTH_INSUFFICIENT").sum()),
                m_lt_10,
            )
            self.assertEqual(
                int(players["calibration_population"].sum()), calibration
            )
            self.assertTrue(
                (players.loc[players["ranking_eligible"], "M_role"] >= MATCH_GATE).all()
            )
            self.assertFalse(
                (
                    players["ranking_eligible"]
                    & (players["M_role"] < MATCH_GATE)
                ).any()
            )
        both = set(
            self.batter_players.loc[
                self.batter_players["ranking_eligible"], "player_id"
            ]
        ) & set(
            self.bowler_players.loc[
                self.bowler_players["ranking_eligible"], "player_id"
            ]
        )
        self.assertEqual(len(both), 23)

    def test_10_calibration_population_and_constants(self):
        """Calibration uses F non-empty without the M>=10 gate."""
        for role, players in (
            ("batter", self.batter_players),
            ("bowler", self.bowler_players),
        ):
            cal = players[players["calibration_population"]]
            self.assertEqual(len(cal), CALIBRATION[role]["n"])
            self.assertTrue(cal["F_nonempty"].all())
            self.assertTrue(np.isfinite(cal["Z_comp"]).all())
            self.assertAlmostEqual(
                float(cal["Z_comp"].mean()),
                CALIBRATION[role]["mu"],
                places=8,
            )
            self.assertAlmostEqual(
                float(cal["Z_comp"].std(ddof=0)),
                CALIBRATION[role]["sigma"],
                places=8,
            )
            # The calibration population includes players below the M gate.
            self.assertGreater(
                int((cal["M_role"] < MATCH_GATE).sum()), 0
            )
            # Every final-ranked player must be in the calibration population.
            ranked_ids = set(
                players.loc[players["ranking_eligible"], "player_id"]
            )
            self.assertTrue(ranked_ids.issubset(set(cal["player_id"])))

    def test_11_reliability_formula(self):
        """Reliability uses the approved calibrated logistic formula."""
        for role, players in (
            ("batter", self.batter_players),
            ("bowler", self.bowler_players),
        ):
            cal = players[players["calibration_population"]]
            expected_z = (
                cal["Z_comp"] - CALIBRATION[role]["mu"]
            ) / CALIBRATION[role]["sigma"]
            expected_rel = 100.0 / (
                1.0 + np.exp(-RELIABILITY_GAMMA * expected_z)
            )
            np.testing.assert_allclose(cal["Z_std"], expected_z, rtol=1e-12)
            np.testing.assert_allclose(
                cal["Reliability"], expected_rel, rtol=1e-12, atol=1e-12
            )
            self.assertTrue(np.isfinite(cal["Reliability"]).all())
            self.assertTrue(cal["Reliability"].between(0, 100).all())
            ranked = players[players["ranking_eligible"]]
            self.assertTrue(np.isfinite(ranked["Reliability"]).all())

    # ------------------------------------------------------------------
    # Ranking, duplicates and top 10
    # ------------------------------------------------------------------
    def test_12_deterministic_ranking_and_top10(self):
        """Ranking order, tie-break fields and top-10 membership are exact."""
        expected_top_ids = {
            "batter": [3374, 4369, 6288, 37052, 2485, 2930, 1699, 2921, 4246, 6651],
            "bowler": [4658, 4840, 7364, 7690, 781, 7699, 1596, 7503, 6643, 8661],
        }
        for role, players, top in (
            ("batter", self.batter_players, self.top_batters),
            ("bowler", self.bowler_players, self.top_bowlers),
        ):
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
            self.assertEqual(
                observed_order["player_id"].tolist(),
                expected_order["player_id"].tolist(),
            )
            self.assertEqual(
                observed_order["final_rank"].tolist(),
                list(range(1, len(observed_order) + 1)),
            )
            self.assertEqual(top["player_id"].tolist(), expected_top_ids[role])
            self.assertEqual(
                top["player_id"].tolist(),
                observed_order.head(10)["player_id"].tolist(),
            )
            self.assertTrue((top["M_role"] >= MATCH_GATE).all())
            self.assertTrue(np.isfinite(top["Z_comp"]).all())
            self.assertTrue(np.isfinite(top["Reliability"]).all())

    def test_13_no_duplicates_missing_values_or_infinite_scores(self):
        """Keys are unique and every ranked score is finite and traceable."""
        for role, records, players in (
            ("batter", self.batter_records, self.batter_players),
            ("bowler", self.bowler_records, self.bowler_players),
        ):
            self.assertFalse(
                records.duplicated(["match_format", "player_id"]).any()
            )
            self.assertFalse(players["player_id"].duplicated().any())
            eligible = players[players["ranking_eligible"]]
            self.assertFalse(eligible["player_id"].duplicated().any())
            self.assertTrue(np.isfinite(eligible["Z_comp"]).all())
            self.assertTrue(np.isfinite(eligible["Z_std"]).all())
            self.assertTrue(np.isfinite(eligible["Reliability"]).all())
            self.assertTrue(eligible["player_name"].notna().all())
            self.assertTrue((eligible["player_name"].astype(str).str.len() > 0).all())
            # Every player-format in F is represented in the format records.
            f_ids = set(
                records.loc[records["composite_ready"], "player_id"]
            )
            player_ids = set(
                players.loc[players["F_nonempty"], "player_id"]
            )
            self.assertEqual(f_ids, player_ids)

    def test_14_independent_validation_suite(self):
        """The independent validation layer reports no failures."""
        checks = run_validation_checks(self.result, check_outputs=False)
        failures = [check for check in checks if not check["passed"]]
        self.assertTrue(
            not failures,
            "\n".join(
                f"[{c['area']}] {c['check']}: {c['detail']}" for c in failures
            ),
        )
        self.assertGreaterEqual(len(checks), 60)


if __name__ == "__main__":
    unittest.main()
