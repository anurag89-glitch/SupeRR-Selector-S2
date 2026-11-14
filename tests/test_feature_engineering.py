"""
Automated Validation Tests for Stage 3: Delivery-Level Feature Engineering
Project: SupeRR Selector Season 2 - Rajasthan Royals IPL 2027
"""

import unittest
from pathlib import Path
import pandas as pd
import numpy as np

PROCESSED_DIR = Path("data/processed")
RAW_DIR = Path("data/raw")


class TestFeatureEngineering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Load feature engineered datasets."""
        cls.primary = pd.read_csv(PROCESSED_DIR / "delivery_pressure_features.csv", dtype={"season": str})
        cls.interrupted = pd.read_csv(PROCESSED_DIR / "interrupted_delivery_features.csv", dtype={"season": str})
        cls.super_over = pd.read_csv(PROCESSED_DIR / "super_over_delivery_features.csv", dtype={"season": str})
        cls.cleaned_matches = pd.read_csv(PROCESSED_DIR / "cleaned_matches.csv")
        cls.raw_matches = pd.read_csv(RAW_DIR / "matches.csv")

    def test_01_dataset_dimensions_and_preservation(self):
        """Test dataset dimensions and total preservation."""
        self.assertEqual(len(self.primary), 192056, "Primary completed deliveries must equal 192,056")
        self.assertEqual(self.primary["match_id"].nunique(), 812, "Completed matches must equal 812")

        self.assertEqual(len(self.interrupted), 1932, "Interrupted deliveries must equal 1,932")
        self.assertEqual(self.interrupted["match_id"].nunique(), 25, "Interrupted matches must equal 25")

        self.assertEqual(len(self.super_over), 26, "Super over deliveries must equal 26")
        self.assertEqual(self.super_over["match_id"].nunique(), 4, "Super over matches must equal 4")

        total_deliveries = len(self.primary) + len(self.interrupted) + len(self.super_over)
        self.assertEqual(total_deliveries, 194014, "Total deliveries across all sets must equal 194,014")

    def test_02_zero_data_leakage(self):
        """Verify that pre-delivery state strictly satisfies zero data leakage."""
        sample_mids = [13512, 14098, 17395, 21586, 40727, 48610, 50371]

        for mid in sample_mids:
            match_df = self.primary[self.primary["match_id"] == mid]
            for inn in match_df["innings"].unique():
                inn_df = match_df[match_df["innings"] == inn].sort_values(
                    ["innings_ball_num", "overid", "over_ball_num"]
                ).reset_index(drop=True)

                first_row = inn_df.iloc[0]
                self.assertEqual(first_row["runs_before"], 0, f"Match {mid} Inn {inn} ball 1 runs_before != 0")
                self.assertEqual(first_row["wickets_before"], 0, f"Match {mid} Inn {inn} ball 1 wickets_before != 0")
                self.assertEqual(first_row["legal_balls_before"], 0, f"Match {mid} Inn {inn} ball 1 legal_balls_before != 0")

                runs_next = inn_df["runs_before"].iloc[1:].values
                runs_calc = (inn_df["runs_before"] + inn_df["team_runs"]).iloc[:-1].values
                np.testing.assert_array_equal(runs_next, runs_calc, f"Runs leakage detected in Match {mid} Inn {inn}")

                wkts_next = inn_df["wickets_before"].iloc[1:].values
                wkts_calc = (inn_df["wickets_before"] + inn_df["is_wicket"].astype(int)).iloc[:-1].values
                np.testing.assert_array_equal(wkts_next, wkts_calc, f"Wickets leakage detected in Match {mid} Inn {inn}")

                legal_next = inn_df["legal_balls_before"].iloc[1:].values
                legal_calc = (inn_df["legal_balls_before"] + inn_df["is_legal_delivery"].astype(int)).iloc[:-1].values
                np.testing.assert_array_equal(legal_next, legal_calc, f"Legal balls leakage detected in Match {mid} Inn {inn}")

    def test_03_wide_followed_immediately_by_legal_delivery(self):
        """Verify that a wide does not increment legal_balls_before, and the subsequent legal ball does."""
        m = self.primary[(self.primary["match_id"] == 14098) & (self.primary["innings"] == 2)].sort_values(
            ["innings_ball_num", "overid", "over_ball_num"]
        ).reset_index(drop=True)

        ball_4_wide = m.iloc[113]  # Over 19 Ball 4: wide
        ball_5_six = m.iloc[114]   # Over 19 Ball 5: legal six
        ball_6_wide = m.iloc[115]  # Over 19 Ball 6: wide

        self.assertEqual(ball_4_wide["extras_type_clean"], "wide")
        self.assertFalse(ball_4_wide["is_legal_delivery"])
        self.assertEqual(ball_4_wide["legal_balls_before"], 111)

        # On ball 5, legal_balls_before MUST STILL be 111 because ball 4 was a wide!
        self.assertEqual(ball_5_six["legal_balls_before"], 111)
        self.assertTrue(ball_5_six["is_legal_delivery"])

        # On ball 6, legal_balls_before must now be 112 because ball 5 was legal!
        self.assertEqual(ball_6_wide["legal_balls_before"], 112)

    def test_04_noball_followed_immediately_by_legal_delivery(self):
        """Verify that a no-ball (other or overstep) does not increment legal_balls_before."""
        m = self.primary[(self.primary["match_id"] == 14098) & (self.primary["innings"] == 2)].sort_values(
            ["innings_ball_num", "overid", "over_ball_num"]
        ).reset_index(drop=True)

        ball_nb = m.iloc[118]    # Over 20 Ball 1: other
        ball_legal = m.iloc[119] # Over 20 Ball 2: legal single
        ball_next = m.iloc[120]  # Over 20 Ball 3: legal single

        self.assertEqual(ball_nb["extras_type_clean"], "other")
        self.assertFalse(ball_nb["is_legal_delivery"])
        self.assertEqual(ball_nb["legal_balls_before"], 114)

        # Ball 2 legal_balls_before must remain 114!
        self.assertEqual(ball_legal["legal_balls_before"], 114)
        self.assertTrue(ball_legal["is_legal_delivery"])

        # Ball 3 legal_balls_before must be 115!
        self.assertEqual(ball_next["legal_balls_before"], 115)

    def test_05_multiple_wides_in_same_over(self):
        """Verify multiple wides in the same over leave legal_balls_before unchanged across occurrences."""
        m = self.primary[(self.primary["match_id"] == 13512) & (self.primary["innings"] == 2)].sort_values(
            ["innings_ball_num", "overid", "over_ball_num"]
        ).reset_index(drop=True)

        over_20 = m[m["overid"] == 20].reset_index(drop=True)
        self.assertEqual(len(over_20), 8)

        # Ball 1 is wide (legal_balls_before = 114)
        self.assertEqual(over_20.iloc[0]["extras_type_clean"], "wide")
        self.assertEqual(over_20.iloc[0]["legal_balls_before"], 114)

        # Ball 2 is dot (legal_balls_before STILL 114)
        self.assertEqual(over_20.iloc[1]["legal_balls_before"], 114)

        # Ball 3 is four (legal_balls_before = 115)
        self.assertEqual(over_20.iloc[2]["legal_balls_before"], 115)

        # Ball 4 is four (legal_balls_before = 116)
        self.assertEqual(over_20.iloc[3]["legal_balls_before"], 116)

        # Ball 5 is wide (legal_balls_before = 117)
        self.assertEqual(over_20.iloc[4]["extras_type_clean"], "wide")
        self.assertEqual(over_20.iloc[4]["legal_balls_before"], 117)

        # Ball 6 is six (legal_balls_before STILL 117)
        self.assertEqual(over_20.iloc[5]["legal_balls_before"], 117)

    def test_06_wicket_and_runs_pre_delivery_isolation(self):
        """Verify current delivery wickets and runs are not in pre-delivery state."""
        m = self.primary[(self.primary["match_id"] == 14098) & (self.primary["innings"] == 2)].sort_values(
            ["innings_ball_num", "overid", "over_ball_num"]
        ).reset_index(drop=True)

        # Wicket isolation
        ball_wkt = m.iloc[116]
        ball_wkt_next = m.iloc[117]
        self.assertTrue(ball_wkt["is_wicket"])
        self.assertEqual(ball_wkt["wickets_before"], 6, "Current wicket must not be in wickets_before!")
        self.assertEqual(ball_wkt_next["wickets_before"], 7)

        # Runs isolation
        ball_six = m.iloc[108]
        ball_six_next = m.iloc[109]
        self.assertEqual(ball_six["runs"], 6)
        self.assertEqual(ball_six["runs_before"], 109, "Current 6 runs must not be in runs_before!")
        self.assertEqual(ball_six_next["runs_before"], 115)

    def test_07_target_provenance_classification_integrity(self):
        """Verify target provenance categories: STANDARD_TARGET, VERIFIED_REVISED_TARGET, UNRESOLVED_TARGET, NOT_APPLICABLE."""
        inn1 = self.primary[self.primary["innings"] == 1]
        inn2 = self.primary[self.primary["innings"] == 2]

        # 1. All Innings 1 deliveries must be NOT_APPLICABLE
        self.assertTrue((inn1["target_provenance"] == "NOT_APPLICABLE").all(), "Innings 1 provenance must be NOT_APPLICABLE")
        self.assertTrue(inn1["target_score"].isna().all(), "Innings 1 target_score must be NaN")

        # 2. Ordinary targets must NOT be mislabeled as revised
        # Matches 17395, 21071, 37354, 40727, 39809, 50137, 50190, 54711 have revised_target == ord_target
        ordinary_curtailed_mids = [17395, 21071, 37354, 40727, 39809, 50137, 50190, 54711]
        for mid in ordinary_curtailed_mids:
            sub = inn2[inn2["match_id"] == mid]
            self.assertTrue((sub["target_provenance"] == "STANDARD_TARGET").all(), f"Match {mid} must be STANDARD_TARGET!")
            first_tot = sub["first_innings_total"].iloc[0]
            self.assertEqual(sub["target_score"].iloc[0], first_tot + 1.0, f"Match {mid} target must be ordinary first_total + 1")

        # 3. Genuinely revised matches must be VERIFIED_REVISED_TARGET (13 completed matches)
        revised_sub = inn2[inn2["target_provenance"] == "VERIFIED_REVISED_TARGET"]
        self.assertEqual(revised_sub["match_id"].nunique(), 13, "Exactly 13 completed matches must be VERIFIED_REVISED_TARGET")
        self.assertTrue(revised_sub["target_score"].notna().all(), "Verified revised targets must be non-null")
        self.assertTrue((revised_sub["runs_required"] >= 0.0).all(), "Runs required must be non-negative")

    def test_08_unresolved_targets_not_used_for_chase_calculations(self):
        """Verify that unresolved targets are not used to calculate runs_required or required_run_rate."""
        inn2 = self.primary[self.primary["innings"] == 2]
        m48610 = inn2[inn2["match_id"] == 48610]

        self.assertEqual(len(m48610), 93)
        self.assertTrue((m48610["target_provenance"] == "UNRESOLVED_TARGET").all(), "Match 48610 must be UNRESOLVED_TARGET")
        self.assertTrue(m48610["target_score"].isna().all(), "Match 48610 target_score must be NaN")
        self.assertTrue(m48610["runs_required"].isna().all(), "Match 48610 runs_required must be NaN")
        self.assertTrue(m48610["required_run_rate"].isna().all(), "Match 48610 required_run_rate must be NaN")
        self.assertFalse(m48610["is_target_reached_before"].any(), "Match 48610 must have zero post-target flags")

    def test_09_raw_revised_target_values_preserved(self):
        """Verify that raw revised_target values in raw matches.csv are completely preserved and unchanged."""
        raw_map = self.raw_matches.set_index("match_id")["revised_target"].dropna().to_dict()
        cleaned_map = self.cleaned_matches.set_index("match_id")["revised_target"].dropna().to_dict()

        for mid, raw_val in raw_map.items():
            if mid in cleaned_map:
                self.assertEqual(cleaned_map[mid], raw_val, f"Raw revised_target for match {mid} was modified!")

        # Explicit check for Match 48610
        self.assertEqual(cleaned_map[48610], 115.0, "Raw revised_target for match 48610 must be 115.0")

    def test_10_target_provenance_and_score_consistency(self):
        """Verify that target_score is strictly consistent with target_provenance."""
        inn2 = self.primary[self.primary["innings"] == 2]

        # Where provenance is NOT_APPLICABLE or UNRESOLVED_TARGET, target_score must be NaN
        unresolved_mask = inn2["target_provenance"].isin(["NOT_APPLICABLE", "UNRESOLVED_TARGET"])
        self.assertTrue(inn2[unresolved_mask]["target_score"].isna().all())

        # Where provenance is STANDARD_TARGET or VERIFIED_REVISED_TARGET, target_score must be non-null and > 0
        resolved_mask = inn2["target_provenance"].isin(["STANDARD_TARGET", "VERIFIED_REVISED_TARGET"])
        self.assertTrue(inn2[resolved_mask]["target_score"].notna().all())
        self.assertTrue((inn2[resolved_mask]["target_score"] > 0).all())


if __name__ == "__main__":
    unittest.main()
