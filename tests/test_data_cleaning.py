"""
Automated Validation Tests for Stage 2: Data Cleaning & Validation
Project: SupeRR Selector Season 2 - Rajasthan Royals IPL 2027
"""

import unittest
from pathlib import Path
import pandas as pd
import json

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


class TestDataCleaningPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Load datasets for testing."""
        cls.raw_matches = pd.read_csv(RAW_DIR / "matches.csv")
        cls.raw_comps = pd.read_csv(RAW_DIR / "competitions.csv")
        cls.raw_balls = pd.read_csv(RAW_DIR / "ball_by_ball.csv")
        cls.raw_teams = pd.read_csv(RAW_DIR / "teams.csv")
        cls.raw_mapping = pd.read_csv(RAW_DIR / "competition_team_player_mapping.csv")

        cls.cleaned_matches = pd.read_csv(PROCESSED_DIR / "cleaned_matches.csv")
        cls.cleaned_deliveries = pd.read_csv(PROCESSED_DIR / "cleaned_deliveries.csv")
        cls.super_over_balls = pd.read_csv(PROCESSED_DIR / "super_over_deliveries.csv")
        cls.interrupted_balls = pd.read_csv(PROCESSED_DIR / "interrupted_matches_deliveries.csv")

        with open(PROCESSED_DIR / "dismissal_dictionary.json", "r", encoding="utf-8") as f:
            cls.dismissal_dict = json.load(f)

    def test_01_raw_files_unmodified(self):
        """Test that original raw files exist and retain original shapes."""
        self.assertEqual(len(self.raw_balls), 200999, "Raw ball_by_ball row count changed!")
        self.assertEqual(len(self.raw_matches), 883, "Raw matches row count changed!")
        self.assertEqual(len(self.raw_comps), 141, "Raw competitions row count changed!")
        self.assertEqual(len(self.raw_teams), 353, "Raw teams row count changed!")
        self.assertEqual(len(self.raw_mapping), 6413, "Raw mapping row count changed!")

    def test_02_match_scope_counts(self):
        """Test IPL (371), T20I (482), total (853), and status breakdowns."""
        self.assertEqual(len(self.cleaned_matches), 853, "Total selected matches must equal 853")

        is_ipl = self.cleaned_matches["comp_name"].str.contains(r"\bIPL\b|Indian Premier League", case=False, na=False)
        is_t20i = self.cleaned_matches["match_format"].eq("T20I")

        self.assertEqual(is_ipl.sum(), 371, "IPL matches must equal 371")
        self.assertEqual(is_t20i.sum(), 482, "T20I matches must equal 482")

        status_counts = self.cleaned_matches["match_status_category"].value_counts().to_dict()
        self.assertEqual(status_counts.get("COMPLETED", 0), 812, "Completed matches must equal 812")
        self.assertEqual(status_counts.get("INTERRUPTED_NO_RESULT", 0), 25, "Interrupted matches must equal 25")
        self.assertEqual(status_counts.get("ABANDONED_NO_BALLS", 0), 16, "Abandoned matches must equal 16")

    def test_03_delivery_counts_and_reconciliation(self):
        """Test exact delivery counts across regular, super over, and interrupted matches."""
        self.assertEqual(len(self.cleaned_deliveries), 194014, "Total selected deliveries must equal 194,014")

        regular_innings = self.cleaned_deliveries[self.cleaned_deliveries["innings"].isin([1, 2])]
        super_overs = self.cleaned_deliveries[self.cleaned_deliveries["innings"].isin([3, 4])]

        self.assertEqual(len(regular_innings), 193988, "Regular innings balls must equal 193,988")
        self.assertEqual(len(super_overs), 26, "Super Over balls must equal 26")
        self.assertEqual(len(self.super_over_balls), 26, "Super over dedicated dataset must have 26 rows")
        self.assertEqual(self.super_over_balls["match_id"].nunique(), 4, "Super overs must span exactly 4 matches")

        self.assertEqual(len(self.interrupted_balls), 1932, "Interrupted match balls must equal 1,932")

    def test_04_runs_and_extras_mathematical_identity(self):
        """Test that team_runs == batter_runs + extras_runs for 100% of deliveries."""
        calculated_team_runs = self.cleaned_deliveries["batter_runs"] + self.cleaned_deliveries["extras_runs"]
        mismatches = (self.cleaned_deliveries["team_runs"] != calculated_team_runs).sum()
        self.assertEqual(mismatches, 0, f"Found {mismatches} rows where team_runs != batter_runs + extras_runs")

        self.assertTrue((self.cleaned_deliveries["batter_runs"] >= 0).all(), "Batter runs must be non-negative")
        self.assertTrue((self.cleaned_deliveries["extras_runs"] >= 0).all(), "Extras runs must be non-negative")
        self.assertTrue((self.cleaned_deliveries["team_runs"] >= 0).all(), "Team runs must be non-negative")

    def test_05_exact_extras_category_counts(self):
        """Explicitly assert exact counts for every extras category in cleaned_deliveries.csv."""
        counts = self.cleaned_deliveries["extras_type_clean"].value_counts().to_dict()

        # Non-legal extras
        self.assertEqual(counts.get("wide", 0), 7474, "Wide count in selected data must be exactly 7,474")
        self.assertEqual(counts.get("overstep", 0), 565, "Overstep count in selected data must be exactly 565")
        self.assertEqual(counts.get("other", 0), 260, "Other count in selected data must be exactly 260")

        # Legal extras and standard deliveries
        self.assertEqual(counts.get("none", 0), 182548, "None (standard) count must be exactly 182,548")
        self.assertEqual(counts.get("legbyes", 0), 2661, "Legbyes count must be exactly 2,661")
        self.assertEqual(counts.get("byes", 0), 505, "Byes count must be exactly 505")
        self.assertEqual(counts.get("penalty", 0), 1, "Penalty count must be exactly 1")

        # Sum of all extras categories must equal 194,014
        total_extras_sum = sum(counts.values())
        self.assertEqual(total_extras_sum, 194014, "Sum of all extras categories must equal exactly 194,014")

    def test_06_legal_vs_non_legal_delivery_reconciliation(self):
        """Verify non-legal and legal delivery classification and exact reconciliation."""
        non_legal_count = (~self.cleaned_deliveries["is_legal_delivery"]).sum()
        legal_count = self.cleaned_deliveries["is_legal_delivery"].sum()

        self.assertEqual(non_legal_count, 8299, "Non-legal deliveries must equal exactly 8,299 (7474 + 565 + 260)")
        self.assertEqual(legal_count, 185715, "Legal deliveries must equal exactly 185,715 (182548 + 2661 + 505 + 1)")
        self.assertEqual(legal_count + non_legal_count, 194014, "Legal + Non-legal deliveries must equal exactly 194,014")

    def test_07_wicket_and_dismissal_attribution(self):
        """Test bowler credited wickets vs team-only wickets."""
        bowler_types = {"Caught", "Bowled", "LBW", "Stump", "Hit Wicket"}
        team_only_types = {"RunOut", "Retire Out", "Obstructing the field"}

        bowler_wickets = self.cleaned_deliveries[self.cleaned_deliveries["is_bowler_wicket"]]
        team_only_wickets = self.cleaned_deliveries[
            self.cleaned_deliveries["is_wicket"] & (~self.cleaned_deliveries["is_bowler_wicket"])
        ]

        self.assertEqual(len(bowler_wickets), 9905, "Bowler-credited wickets must equal 9,905")
        self.assertEqual(len(team_only_wickets), 581, "Team-only dismissals must equal 581")
        self.assertEqual(
            len(bowler_wickets) + len(team_only_wickets),
            self.cleaned_deliveries["is_wicket"].sum(),
            "Sum of bowler and team wickets must equal total wickets"
        )

        invalid_bowler_types = bowler_wickets[~bowler_wickets["dismissal_type_clean"].isin(bowler_types)]
        self.assertEqual(len(invalid_bowler_types), 0, "Invalid dismissal type found in bowler wickets!")

        invalid_team_types = team_only_wickets[~team_only_wickets["dismissal_type_clean"].isin(team_only_types)]
        self.assertEqual(len(invalid_team_types), 0, "Invalid dismissal type found in team-only wickets!")

    def test_08_referential_integrity(self):
        """Test player and team referential integrity."""
        valid_player_ids = set(self.raw_mapping["player_id"].dropna().unique())
        valid_team_ids = set(self.raw_teams["team_id"].dropna().unique())

        delivery_strikers = set(self.cleaned_deliveries["striker_id"].dropna().unique())
        delivery_bowlers = set(self.cleaned_deliveries["bowler_id"].dropna().unique())
        delivery_batting_teams = set(self.cleaned_deliveries["batting_team_id"].dropna().unique())
        delivery_bowling_teams = set(self.cleaned_deliveries["bowling_team_id"].dropna().unique())

        self.assertTrue(delivery_strikers.issubset(valid_player_ids), "Unmapped striker IDs found!")
        self.assertTrue(delivery_bowlers.issubset(valid_player_ids), "Unmapped bowler IDs found!")
        self.assertTrue(delivery_batting_teams.issubset(valid_team_ids), "Unmapped batting team IDs found!")
        self.assertTrue(delivery_bowling_teams.issubset(valid_team_ids), "Unmapped bowling team IDs found!")

    def test_09_match_48610_exact_record_reconciliation(self):
        """Test Match 48610 records without modifying raw revised_target."""
        match_row = self.cleaned_matches[self.cleaned_matches["match_id"] == 48610].iloc[0]
        self.assertTrue(match_row["has_dls_target_discrepancy"], "Match 48610 must have discrepancy flag")
        self.assertEqual(match_row["revised_target"], 115.0, "Raw revised_target 115.0 must remain unmodified")
        self.assertEqual(match_row["first_inn_revised_overs"], 102.0, "First inn revised overs must be 102.0 (17.0 ov)")
        self.assertEqual(match_row["second_inn_revised_overs"], 90.0, "Second inn revised overs must be 90.0 (15.0 ov)")
        self.assertEqual(match_row["result"], "England Won by 11 runs (DLS method)")

        m_balls = self.cleaned_deliveries[self.cleaned_deliveries["match_id"] == 48610]
        inn1 = m_balls[m_balls["innings"] == 1]
        inn2 = m_balls[m_balls["innings"] == 2]

        # Innings 1: Sri Lanka (27) batted first: 133 all out in 101 balls (98 legal balls = 16.2 ov)
        self.assertEqual(inn1["batting_team_id"].iloc[0], 27, "Innings 1 batting team must be Sri Lanka (27)")
        self.assertEqual(inn1["team_runs"].sum(), 133, "Innings 1 total runs must be 133")
        self.assertEqual(inn1["is_wicket"].sum(), 10, "Innings 1 wickets must be 10")

        # Innings 2: England (22) batted second: 125/4 in 93 balls (90 legal balls = 15.0 ov)
        self.assertEqual(inn2["batting_team_id"].iloc[0], 22, "Innings 2 batting team must be England (22)")
        self.assertEqual(inn2["team_runs"].sum(), 125, "Innings 2 total runs must be 125")
        self.assertEqual(inn2["is_wicket"].sum(), 4, "Innings 2 wickets must be 4")
        self.assertEqual(inn2["is_legal_delivery"].sum(), 90, "Innings 2 legal balls must be exactly 90 (15.0 ov)")


if __name__ == "__main__":
    unittest.main()
