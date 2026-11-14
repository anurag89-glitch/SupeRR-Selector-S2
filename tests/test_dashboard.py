"""Stage 7 dashboard regression tests.

The dashboard is a presentation layer over the approved Stage 5 and Stage 6
CSV outputs.  These tests verify that the app starts, that every page and
scenario renders, that displayed rankings match the source CSVs exactly, and
that the approved result counts remain intact.  They do not write outputs.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "dashboard" / "app.py"
STAGE5_DIR = PROJECT_ROOT / "outputs" / "stage5"
STAGE6_DIR = PROJECT_ROOT / "outputs" / "stage6"

sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _load_dashboard_module():
    spec = importlib.util.spec_from_file_location("dashboard_app_tests", APP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_clean(at: AppTest) -> None:
    assert not at.exception, [exception.value for exception in at.exception]
    assert not at.error, [error.value for error in at.error]


def _open_page(page: str) -> AppTest:
    at = AppTest.from_file(str(APP_PATH), default_timeout=120).run()
    _assert_clean(at)
    at.radio(key="navigation").set_value(page).run()
    _assert_clean(at)
    return at


def _assert_top10_matches_csv(table: pd.DataFrame, role: str) -> None:
    source = pd.read_csv(STAGE5_DIR / f"top10_{role}s.csv")
    assert len(table) == 10
    assert list(table["Player ID"]) == list(source["player_id"])
    assert list(table["Player"]) == list(source["player_name"])
    assert list(table["Rank"]) == list(source["final_rank"])
    np.testing.assert_allclose(
        table["Composite Z"].to_numpy(float),
        source["Z_comp"].to_numpy(float),
        rtol=0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        table["Reliability"].to_numpy(float),
        source["Reliability"].to_numpy(float),
        rtol=0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        table["N_eff"].to_numpy(float),
        source["sum_N_eff_del_F"].to_numpy(float),
        rtol=0,
        atol=1e-9,
    )
    assert list(table["Matches"]) == list(source["M_role"])
    assert list(table["N_raw"]) == list(source["sum_N_raw_F"])
    assert list(table["Eligible formats"]) == [
        value.replace(",", " + ") for value in source["F_formats"]
    ]


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_module()
        cls.data = cls.dashboard.prepare_data(cls.dashboard.load_data())

    def test_required_outputs_and_approved_counts(self):
        required = {
            "batter_scoring",
            "bowler_scoring",
            "batter_format",
            "bowler_format",
            "top10_batter",
            "top10_bowler",
            "batter_sensitivity",
            "bowler_sensitivity",
            "player_rank_changes",
            "sensitivity_summary",
            "batter_stability",
            "bowler_stability",
            "eligibility_sensitivity",
            "scenario_diagnostics",
            "validation_checks",
        }
        self.assertTrue(required.issubset(self.data))

        batter = self.data["batter_scoring"]
        bowler = self.data["bowler_scoring"]
        batter_ids = set(batter.loc[batter["ranking_eligible"], "player_id"])
        bowler_ids = set(bowler.loc[bowler["ranking_eligible"], "player_id"])
        self.assertEqual(len(batter_ids), 101)
        self.assertEqual(len(bowler_ids), 141)
        self.assertEqual(len(batter_ids & bowler_ids), 23)
        self.assertEqual(len(batter), 746)
        self.assertEqual(len(bowler), 507)

        summary = self.data["sensitivity_summary"]
        approved_completed = summary[
            (summary["approved"] == True)  # noqa: E712 - explicit boolean column
            & summary["status"].isin(["PRIMARY", "COMPLETED"])
        ]
        mandatory_completed = summary[
            (summary["mandatory"] == True)  # noqa: E712
            & (summary["scenario_id"] != "PRIMARY")
        ]
        self.assertEqual(len(approved_completed), 21)
        self.assertEqual(len(mandatory_completed), 20)
        self.assertTrue(mandatory_completed["status"].eq("COMPLETED").all())
        self.assertEqual(
            summary["status"]
            .isin(["PRIMARY", "COMPLETED", "COMPLETED_SUPPLEMENTARY"])
            .sum(),
            31,
        )
        self.assertEqual(
            (summary["status"] == "BLOCKED_NOT_APPROVED").sum(), 1
        )
        self.assertEqual((summary["status"] == "OPTIONAL_NOT_RUN").sum(), 1)

        checks = self.data["validation_checks"]
        self.assertEqual(len(checks), 23)
        self.assertTrue(checks["passed"].all())

        self.assertEqual(
            list(self.data["top10_batter"]["player_id"]),
            [3374, 4369, 6288, 37052, 2485, 2930, 1699, 2921, 4246, 6651],
        )
        self.assertEqual(
            list(self.data["top10_bowler"]["player_id"]),
            [4658, 4840, 7364, 7690, 781, 7699, 1596, 7503, 6643, 8661],
        )

    def test_overview_page_kpis_and_snapshot(self):
        at = _open_page("Overview")
        page_text = "\n".join(element.value for element in at.markdown)
        for expected in (
            "SupeRR Selector",
            "812",
            "191,963",
            "Eligible batters",
            "101",
            "Eligible bowlers",
            "141",
            "Dual-role players",
            "23",
            "20 approved alternatives",
        ):
            self.assertIn(expected, page_text)
        self.assertEqual(len(at.dataframe), 2)
        _assert_top10_matches_csv(at.dataframe[0].value, "batter")
        _assert_top10_matches_csv(at.dataframe[1].value, "bowler")
        self.assertEqual(len(at.get("plotly_chart")), 1)

    def test_top10_tables_match_source_csv(self):
        at = _open_page("Top 10 Batters")
        self.assertEqual(len(at.dataframe), 2)
        _assert_top10_matches_csv(at.dataframe[0].value, "batter")
        _assert_top10_matches_csv(at.dataframe[1].value, "batter")

        at.radio(key="navigation").set_value("Top 10 Bowlers").run()
        _assert_clean(at)
        self.assertEqual(len(at.dataframe), 2)
        _assert_top10_matches_csv(at.dataframe[0].value, "bowler")
        _assert_top10_matches_csv(at.dataframe[1].value, "bowler")

    def test_top10_search_filter_sort_and_clear(self):
        at = _open_page("Top 10 Batters")

        at.text_input(key="top10_query_batter").set_value("Mark Chapman").run()
        _assert_clean(at)
        self.assertEqual(len(at.dataframe[0].value), 1)
        self.assertEqual(at.dataframe[0].value.iloc[0]["Player ID"], 3374)

        at.selectbox(key="top10_format_batter").set_value("T20I").run()
        _assert_clean(at)
        self.assertEqual(len(at.dataframe[0].value), 1)
        self.assertIn("T20I", at.dataframe[0].value.iloc[0]["Eligible formats"])

        at.selectbox(key="top10_sort_batter").set_value(
            "Reliability (high to low)"
        ).run()
        _assert_clean(at)
        reliability = at.dataframe[0].value["Reliability"].to_numpy(float)
        self.assertTrue(np.all(np.diff(reliability) <= 0))

        at.text_input(key="top10_query_batter").set_value("no-such-player").run()
        _assert_clean(at)
        self.assertTrue(
            any("No top-10 player matches" in info.value for info in at.info)
        )

        clear = [
            button
            for button in at.button
            if button.key == "top10_clear_batter"
        ]
        self.assertEqual(len(clear), 1)
        clear[0].click().run()
        _assert_clean(at)
        self.assertEqual(at.text_input(key="top10_query_batter").value, "")
        self.assertEqual(
            at.selectbox(key="top10_format_batter").value, "All formats"
        )
        self.assertEqual(
            at.selectbox(key="top10_sort_batter").value, "Final rank"
        )
        self.assertEqual(len(at.dataframe[0].value), 10)

        at.text_input(key="top10_query_batter").set_value("3374").run()
        _assert_clean(at)
        self.assertEqual(len(at.dataframe[0].value), 1)
        self.assertEqual(at.dataframe[0].value.iloc[0]["Player"], "Mark Chapman")
        at.text_input(key="top10_query_batter").set_value("").run()
        _assert_clean(at)

        at.selectbox(key="top10_format_batter").set_value("IPL").run()
        _assert_clean(at)
        self.assertGreater(len(at.dataframe[0].value), 0)
        self.assertTrue(
            at.dataframe[0].value["Eligible formats"].str.contains("IPL").all()
        )

    def test_top10_audit_view_exposes_approved_z_std(self):
        at = _open_page("Top 10 Batters")
        for role, page in (
            ("batters", "Top 10 Batters"),
            ("bowlers", "Top 10 Bowlers"),
        ):
            if role == "bowlers":
                at.radio(key="navigation").set_value(page).run()
                _assert_clean(at)
            self.assertEqual(len(at.dataframe), 2)
            audit = at.dataframe[1].value
            source = pd.read_csv(STAGE5_DIR / f"top10_{role}.csv")
            self.assertIn("Z_std", audit.columns)
            self.assertEqual(len(audit), 10)
            np.testing.assert_allclose(
                audit["Z_std"].to_numpy(float),
                source["Z_std"].to_numpy(float),
                rtol=0,
                atol=1e-12,
            )

    def test_comparison_category_filter_scopes_scenarios(self):
        at = _open_page("Ranking Comparison")
        self.assertEqual(at.selectbox(key="comparison_category").value, "all")
        self.assertEqual(
            len(at.selectbox(key="comparison_scenario").options), 21
        )
        self.assertFalse(
            any(
                "SUPP_" in option
                for option in at.selectbox(key="comparison_scenario").options
            )
        )

        at.selectbox(key="comparison_category").set_value(
            "approved_grid"
        ).run()
        _assert_clean(at)
        grid = at.selectbox(key="comparison_scenario").options
        self.assertEqual(len(grid), 6)
        self.assertTrue(all("Approved grid" in option for option in grid))

        at.selectbox(key="comparison_category").set_value(
            "approved_mandatory"
        ).run()
        _assert_clean(at)
        mandatory = at.selectbox(key="comparison_scenario").options
        self.assertEqual(len(mandatory), 14)
        self.assertTrue(
            all("Approved mandatory" in option for option in mandatory)
        )
        self.assertNotIn(
            "Supplementary — diagnostic",
            at.selectbox(key="comparison_category").options,
        )

        at.toggle(key="include_supplementary").set_value(True).run()
        _assert_clean(at)
        self.assertIn(
            "Supplementary — diagnostic",
            at.selectbox(key="comparison_category").options,
        )
        at.selectbox(key="comparison_category").set_value("all").run()
        _assert_clean(at)
        self.assertEqual(
            len(at.selectbox(key="comparison_scenario").options), 31
        )
        self.assertTrue(
            any(
                "SUPP_SIGMA_8" in option
                for option in at.selectbox(key="comparison_scenario").options
            )
        )
        at.selectbox(key="comparison_category").set_value(
            "supplementary_non_approved"
        ).run()
        _assert_clean(at)
        self.assertEqual(
            len(at.selectbox(key="comparison_scenario").options), 10
        )
        at.selectbox(key="comparison_scenario").set_value(
            "SUPP_SIGMA_8"
        ).run()
        _assert_clean(at)
        self.assertEqual(len(at.dataframe), 6)
        self.assertEqual(len(at.get("plotly_chart")), 4)

        at.toggle(key="include_supplementary").set_value(False).run()
        _assert_clean(at)
        self.assertEqual(
            at.selectbox(key="comparison_category").value, "all"
        )
        self.assertEqual(
            at.selectbox(key="comparison_scenario").value, "P_65"
        )
        self.assertEqual(
            len(at.selectbox(key="comparison_scenario").options), 21
        )
        self.assertFalse(
            any(
                "SUPP_" in option
                for option in at.selectbox(key="comparison_scenario").options
            )
        )

    def test_download_controls_present_on_data_pages(self):
        at = _open_page("Top 10 Batters")
        self.assertEqual(
            [button.label for button in at.get("download_button")],
            ["Download filtered table (CSV)"],
        )
        self.assertTrue(
            all(not button.disabled for button in at.get("download_button"))
        )

        at.radio(key="navigation").set_value("Player Analysis").run()
        _assert_clean(at)
        self.assertEqual(
            [button.label for button in at.get("download_button")],
            ["Download full approved record (CSV)"],
        )

        at.radio(key="navigation").set_value("Ranking Comparison").run()
        _assert_clean(at)
        self.assertEqual(
            [button.label for button in at.get("download_button")],
            [
                "Download batter movement table (CSV)",
                "Download bowler movement table (CSV)",
            ],
        )

    def test_player_search_id_and_role_switch(self):
        at = _open_page("Player Analysis")

        at.text_input(key="player_search").set_value("1596").run()
        _assert_clean(at)
        self.assertEqual(at.selectbox(key="player_select").value, 1596)

        at.selectbox(key="player_select").set_value(1596).run()
        _assert_clean(at)
        role_radio = at.radio(key="player_role")
        self.assertEqual(role_radio.options, ["Batter", "Bowler"])
        self.assertEqual(role_radio.value, "batter")
        self.assertTrue(
            any("Moeen Ali" in element.value for element in at.markdown)
        )

        role_radio.set_value("bowler").run()
        _assert_clean(at)
        self.assertEqual(at.radio(key="player_role").value, "bowler")
        self.assertEqual(len(at.dataframe), 3)
        self.assertEqual(len(at.get("plotly_chart")), 3)
        self.assertIn("Format Z", at.dataframe[1].value.columns)
        self.assertGreaterEqual(len(at.dataframe[2].value), 1)

        at.text_input(key="player_search").set_value("Moeen Ali").run()
        _assert_clean(at)
        self.assertEqual(at.selectbox(key="player_select").value, 1596)

    def test_player_analysis_empty_and_noneligible_paths(self):
        at = _open_page("Player Analysis")

        at.text_input(key="player_search").set_value("zzzz-no-player").run()
        _assert_clean(at)
        self.assertTrue(
            any("No player matches" in warning.value for warning in at.warning)
        )

        at.text_input(key="player_search").set_value("Ishant Sharma").run()
        _assert_clean(at)
        at.selectbox(key="player_select").set_value(28).run()
        _assert_clean(at)
        self.assertTrue(
            any("Not in the primary" in info.value for info in at.info)
        )
        self.assertEqual(len(at.dataframe), 3)
        # Missing values are rendered as an em dash rather than crashing.
        page_text = "\n".join(element.value for element in at.markdown)
        self.assertIn("—", page_text)

    def test_ranking_comparison_tables_and_membership(self):
        at = _open_page("Ranking Comparison")
        self.assertEqual(at.selectbox(key="comparison_scenario").value, "P_65")
        self.assertEqual(len(at.dataframe), 6)
        self.assertEqual(len(at.get("plotly_chart")), 4)

        at.selectbox(key="comparison_scenario").set_value("K_25").run()
        _assert_clean(at)
        for role in ("batter", "bowler"):
            comparison = self.dashboard._comparison_table(self.data, role, "K_25")
            self.assertEqual(len(comparison), 10)
            self.assertEqual(set(comparison["Membership"]), {"Retained"})

        for role, overlap, entrants, leavers in (
            ("batter", 9, 1, 1),
            ("bowler", 6, 4, 4),
        ):
            comparison = self.dashboard._comparison_table(
                self.data, role, "NRAW_100"
            )
            self.assertEqual(
                (comparison["Membership"] == "Retained").sum(), overlap
            )
            self.assertEqual(
                (comparison["Membership"] == "Entrant").sum(), entrants
            )
            self.assertEqual(
                (comparison["Membership"] == "Leaver").sum(), leavers
            )
            self.assertEqual(len(comparison), 10 + entrants)

        at.selectbox(key="comparison_scenario").set_value("NRAW_100").run()
        _assert_clean(at)
        self.assertEqual(
            at.selectbox(key="comparison_scenario").value, "NRAW_100"
        )

    def test_comparison_supplementary_toggle_and_all_scenarios(self):
        at = _open_page("Ranking Comparison")
        at.toggle(key="include_supplementary").set_value(True).run()
        _assert_clean(at)
        options = at.selectbox(key="comparison_scenario").options
        self.assertEqual(len(options), 31)
        self.assertTrue(any("SUPP_SIGMA_8" in option for option in options))

        at.selectbox(key="comparison_scenario").set_value("SUPP_SIGMA_8").run()
        _assert_clean(at)
        self.assertEqual(
            at.selectbox(key="comparison_scenario").value, "SUPP_SIGMA_8"
        )
        self.assertTrue(
            any("Supplementary" in element.value for element in at.markdown)
        )

        scenario_ids = self.data["sensitivity_summary"].loc[
            self.data["sensitivity_summary"]["status"].isin(
                ["PRIMARY", "COMPLETED", "COMPLETED_SUPPLEMENTARY"]
            ),
            "scenario_id",
        ]
        self.assertEqual(len(scenario_ids), 31)
        for scenario_id in scenario_ids:
            at.selectbox(key="comparison_scenario").set_value(scenario_id).run()
            _assert_clean(at)
            self.assertEqual(
                at.selectbox(key="comparison_scenario").value, scenario_id
            )
            self.assertEqual(len(at.dataframe), 6)
            self.assertEqual(len(at.get("plotly_chart")), 4)

    def test_methodology_validation_and_limitations(self):
        at = _open_page("Data and Methodology")
        self.assertEqual(
            [tab.label for tab in at.tabs],
            [
                "Coverage",
                "Eligibility",
                "Scoring",
                "Reliability",
                "Limitations",
                "Validation",
            ],
        )
        self.assertEqual(len(at.dataframe), 5)

        coverage = at.dataframe[0].value
        self.assertEqual(len(coverage), 8)
        coverage_text = coverage.to_string()
        for expected in ("191,963", "192,056", "87,217", "104,746"):
            self.assertIn(expected, coverage_text)

        checks = at.dataframe[3].value
        self.assertEqual(len(checks), 23)
        self.assertTrue(checks["Passed"].all())

        registry = at.dataframe[4].value
        self.assertEqual(len(registry), 33)
        self.assertEqual((registry["Status"] == "COMPLETED").sum(), 20)
        self.assertEqual(
            (registry["Status"] == "COMPLETED_SUPPLEMENTARY").sum(), 10
        )
        self.assertEqual(
            (registry["Status"] == "BLOCKED_NOT_APPROVED").sum(), 1
        )
        self.assertEqual((registry["Status"] == "OPTIONAL_NOT_RUN").sum(), 1)

        page_text = "\n".join(element.value for element in at.markdown)
        for expected in (
            "PROVISIONAL_OTHER",
            "Match 48610",
            "93 second-innings rows",
            "9,816",
            "9,827",
            "Wide-stumping asymmetry",
            "25 wide stumpings",
            "No combined all-rounder ranking",
            "Retire Out",
        ):
            self.assertIn(expected, page_text)

    def test_chart_builders_cover_all_players_and_scenarios(self):
        for role in ("batter", "bowler"):
            self.dashboard.top10_bar(self.data[f"top10_{role}"], role)
            self.dashboard.scenario_correlation_chart(
                self.data["sensitivity_summary"],
                role,
                self.data["sensitivity_summary"]["scenario_id"].tolist(),
            )
            for scenario_id in self.data["sensitivity_summary"]["scenario_id"]:
                comparison = self.dashboard._comparison_table(
                    self.data, role, scenario_id
                )
                self.dashboard.scenario_bump_chart(
                    comparison, scenario_id, role
                )

            scoring = self.data[f"{role}_scoring"]
            records = self.data[f"{role}_format"]
            for player_id in scoring.loc[
                scoring["ranking_eligible"], "player_id"
            ]:
                player_records = records[records["player_id"] == player_id]
                self.dashboard.pressure_chart(player_records, role)
                self.dashboard.format_score_chart(player_records, role)
                self.dashboard.reliability_chart(
                    scoring, int(player_id), role
                )

        self.dashboard.eligibility_chart(self.data)

    def test_primary_rankings_and_stage6_outputs_unchanged(self):
        batter = pd.read_csv(STAGE5_DIR / "batter_scoring.csv")
        bowler = pd.read_csv(STAGE5_DIR / "bowler_scoring.csv")
        batter_top10 = pd.read_csv(STAGE5_DIR / "top10_batters.csv")
        bowler_top10 = pd.read_csv(STAGE5_DIR / "top10_bowlers.csv")

        self.assertEqual(int(batter["ranking_eligible"].sum()), 101)
        self.assertEqual(int(bowler["ranking_eligible"].sum()), 141)
        self.assertEqual(
            list(batter_top10["player_id"]),
            list(
                batter.loc[batter["ranking_eligible"]]
                .sort_values("final_rank")
                .head(10)["player_id"]
            ),
        )
        self.assertEqual(
            list(bowler_top10["player_id"]),
            list(
                bowler.loc[bowler["ranking_eligible"]]
                .sort_values("final_rank")
                .head(10)["player_id"]
            ),
        )

        for role, source, baseline in (
            ("batter", "batter_sensitivity_rankings.csv", batter),
            ("bowler", "bowler_sensitivity_rankings.csv", bowler),
        ):
            sensitivity = pd.read_csv(STAGE6_DIR / source)
            primary = sensitivity[
                sensitivity["scenario_id"] == "PRIMARY"
            ].copy()
            eligible = baseline[baseline["ranking_eligible"]][
                ["player_id", "final_rank", "Z_comp", "Reliability"]
            ]
            merged = primary.merge(
                eligible,
                on="player_id",
                suffixes=("_scenario", "_stage5"),
                validate="one_to_one",
            )
            self.assertEqual(len(merged), len(eligible))
            self.assertTrue(
                (
                    merged["final_rank_scenario"]
                    == merged["final_rank_stage5"]
                ).all()
            )
            # The CSV outputs are rounded to 10 decimal places; the scenario
            # engine and Stage 5 scoring can differ only at that precision.
            np.testing.assert_allclose(
                merged["Z_comp_scenario"],
                merged["Z_comp_stage5"],
                rtol=0,
                atol=1e-9,
            )
            np.testing.assert_allclose(
                merged["Reliability_scenario"],
                merged["Reliability_stage5"],
                rtol=0,
                atol=1e-9,
            )

        summary = pd.read_csv(STAGE6_DIR / "sensitivity_summary.csv")
        mandatory = summary[
            (summary["mandatory"] == True)  # noqa: E712
            & (summary["scenario_id"] != "PRIMARY")
        ]
        self.assertEqual(len(mandatory), 20)
        self.assertTrue(mandatory["status"].eq("COMPLETED").all())

        checks = pd.read_csv(STAGE6_DIR / "stage6_validation_checks.csv")
        self.assertEqual(len(checks), 23)
        self.assertTrue(checks["passed"].all())


if __name__ == "__main__":
    unittest.main()
