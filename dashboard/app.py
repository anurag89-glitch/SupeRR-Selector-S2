"""SupeRR Selector — Stage 7 interactive analytics dashboard.

This app is a read-only presentation layer over the approved Stage 5 scoring
outputs and Stage 6 sensitivity outputs. It never recalculates, rescales or
re-ranks a player; every score shown comes directly from the approved CSVs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from charts import (  # noqa: E402
    eligibility_chart,
    format_score_chart,
    pressure_chart,
    reliability_chart,
    scenario_bump_chart,
    scenario_correlation_chart,
    top10_bar,
)
from components import badge, fmt_int  # noqa: E402
from core import (  # noqa: E402
    DATA_FILES,
    PROJECT_ROOT,
    ROLE_LABELS,
    STAGE5_DIR,
    STAGE6_DIR,
    _bool,
    _clear_top10_filters,
    _comparison_table,
    _movement_display,
    _movement_tables,
    load_data,
    prepare_data,
    top10_column_config,
    top10_display,
    top10_view,
)
from pages import (  # noqa: E402
    render_data_methodology,
    render_overview,
    render_player_analysis,
    render_ranking_comparison,
    render_top10,
)
from theme import CSS  # noqa: E402

NAV_ITEMS = [
    "Overview",
    "Top 10 Batters",
    "Top 10 Bowlers",
    "Player Analysis",
    "Ranking Comparison",
    "Data and Methodology",
]


def render_sidebar(data: dict) -> str:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="mark">SR</div>
          <h2>SupeRR Selector</h2>
          <p>Pressure-adjusted cricket analytics · Season 2</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section-label">Workspace</div>',
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navigate",
        NAV_ITEMS,
        index=0,
        label_visibility="collapsed",
        key="navigation",
    )

    summary = data["sensitivity_summary"]
    primary = summary[summary["scenario_id"] == "PRIMARY"].iloc[0]
    passed = int(data["validation_checks"]["passed"].fillna(False).astype(bool).sum())
    total = len(data["validation_checks"])
    st.markdown(
        f"""
        <div class="sidebar-status">
          <div class="status-row"><span class="dot"></span>Stage 5 primary rankings locked</div>
          <div class="status-row"><span class="dot"></span>Stage 6 validation {passed}/{total} checks</div>
          <div class="status-row"><span class="dot"></span>47/47 Stage 1–6 tests</div>
          <div class="status-row"><span class="dot"></span>{int(primary['matches']):,} matches · {int(primary['corpus_rows']):,} deliveries</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section-label">Display</div>',
        unsafe_allow_html=True,
    )
    st.toggle(
        "Include supplementary scenarios",
        value=False,
        key="include_supplementary",
        help=(
            "Show the non-approved σ, h, leverage and wide-stumping diagnostics in "
            "Ranking Comparison. Approved scenarios are shown by default."
        ),
    )
    st.caption(
        "Affects the Ranking Comparison scenario choices and correlation chart. "
        "Primary scores are never recalculated."
    )

    with st.expander("Data sources", expanded=False):
        st.markdown(
            """
            - `outputs/stage5/batter_scoring.csv`
            - `outputs/stage5/bowler_scoring.csv`
            - `outputs/stage5/*_format_records.csv`
            - `outputs/stage5/top10_*.csv`
            - `outputs/stage6/*.csv`
            - `reports/stage5_scoring_validation.md`
            - `reports/stage6_sensitivity_report.md`
            """
        )
    with st.expander("About this build", expanded=False):
        st.markdown(
            """
            Stage 7 is a read-only presentation layer. It does not modify raw data,
            pressure features, Stage 5 scores/ranks, or Stage 6 sensitivity results.
            The approved CSVs remain the authoritative record.
            """
        )
    st.caption("Read-only · approved Stage 5 and Stage 6 outputs")
    return page


def main() -> None:
    st.set_page_config(
        page_title="SupeRR Selector — Pressure Analytics",
        page_icon="🏏",
        layout="wide",
        initial_sidebar_state="auto",
    )
    st.markdown(CSS, unsafe_allow_html=True)

    try:
        raw = load_data()
        data = prepare_data(raw)
    except Exception as exc:  # pragma: no cover - defensive UI path
        st.error(
            f"Could not load the approved Stage 5/6 outputs: {exc}",
            icon=":material/error:",
        )
        st.stop()

    with st.sidebar:
        page = render_sidebar(data)

    if page == "Overview":
        render_overview(data)
    elif page == "Top 10 Batters":
        render_top10(data, "batter")
    elif page == "Top 10 Bowlers":
        render_top10(data, "bowler")
    elif page == "Player Analysis":
        render_player_analysis(data)
    elif page == "Ranking Comparison":
        render_ranking_comparison(data)
    elif page == "Data and Methodology":
        render_data_methodology(data)

    st.markdown(
        '<div class="footer">SupeRR Selector · Stage 7 interactive dashboard. '
        "Built from approved Stage 5 scoring outputs and Stage 6 sensitivity outputs. "
        "No raw data, pressure features, primary scores, rankings, or sensitivity "
        "results were modified. Pressure scores are situational, not performance scores.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
