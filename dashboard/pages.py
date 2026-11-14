"""Page renderers for the SupeRR Selector dashboard.

The pages are a read-only view over the approved CSV outputs.  All filtering,
sorting and formatting here is display-only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from charts import (
    eligibility_chart,
    format_score_chart,
    pressure_chart,
    reliability_chart,
    scenario_bump_chart,
    scenario_correlation_chart,
    top10_bar,
)
from components import (
    badge,
    esc,
    fmt_formats,
    fmt_int,
    fmt_num,
    fmt_signed,
    fmt_status,
    fmt_text,
    format_category,
    kv_rows,
    metric_grid,
    page_header,
    panel,
    section_heading,
    tag,
    tag_row,
)
from core import (
    ROLE_LABELS,
    _clear_top10_filters,
    _comparison_table,
    _movement_display,
    _movement_tables,
    top10_column_config,
    top10_display,
    top10_view,
)
from theme import CATEGORY_LABELS, COLORS

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


def _plot(fig) -> None:
    if fig is None:
        return
    st.plotly_chart(fig, width="stretch", theme=None, config=PLOT_CONFIG)


def _podium_card(row: pd.Series, rank: int) -> str:
    klass = "podium-card rank-1" if rank == 1 else "podium-card"
    return (
        f'<div class="{klass}">'
        f'<div class="podium-rank">#{rank} · Approved rank</div>'
        f'<div class="podium-name">{esc(row["player_name"])}</div>'
        f'<div class="podium-meta">{esc(fmt_formats(row["F_formats"]))} · '
        f'{fmt_int(row["M_role"])} matches</div>'
        f'<div class="podium-score"><strong>Z {fmt_num(row["Z_comp"], 3)}</strong>'
        f'<span>reliability {fmt_num(row["Reliability"], 1)}</span></div>'
        "</div>"
    )


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------


def render_overview(data: dict[str, pd.DataFrame]) -> None:
    summary = data["sensitivity_summary"]
    primary = summary[summary["scenario_id"] == "PRIMARY"].iloc[0]
    batter_eligible = int(data["batter_scoring"]["ranking_eligible"].sum())
    bowler_eligible = int(data["bowler_scoring"]["ranking_eligible"].sum())
    batter_ids = set(
        data["batter_scoring"].loc[
            data["batter_scoring"]["ranking_eligible"], "player_id"
        ]
    )
    bowler_ids = set(
        data["bowler_scoring"].loc[
            data["bowler_scoring"]["ranking_eligible"], "player_id"
        ]
    )
    dual_role = len(batter_ids & bowler_ids)
    completed = int(
        summary["status"]
        .isin(["PRIMARY", "COMPLETED", "COMPLETED_SUPPLEMENTARY"])
        .sum()
    )
    approved = int(
        ((summary["approved"] == True) & (summary["status"].isin(["PRIMARY", "COMPLETED"]))).sum()  # noqa: E712
    )
    top_batter = data["top10_batter"].sort_values("final_rank").iloc[0]
    top_bowler = data["top10_bowler"].sort_values("final_rank").iloc[0]

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-copy">
            <div class="hero-kicker">SupeRR Selector · Season 2</div>
            <h1>SupeRR Selector</h1>
            <p>
              A decision-support view of the approved pressure-adjusted player rankings
              for IPL and T20I cricket. Inspect the primary top 10, open complete player
              records, and stress-test ranking stability across the approved Stage 6
              sensitivity programme.
            </p>
            <div class="hero-tags">
              <span class="tag green">Stage 5 primary rankings locked</span>
              <span class="tag blue">20 approved alternatives</span>
              <span class="tag">Read-only presentation layer</span>
            </div>
          </div>
          <div class="hero-aside">
            <div class="hero-aside-head">Approved snapshot</div>
            <div class="hero-stat">
              <span class="label">No. 1 batter</span>
              <span class="name">{esc(top_batter["player_name"])}</span>
              <span class="meta">Z {fmt_num(top_batter["Z_comp"], 3)} · Reliability {fmt_num(top_batter["Reliability"], 1)}</span>
            </div>
            <div class="hero-stat">
              <span class="label">No. 1 bowler</span>
              <span class="name">{esc(top_bowler["player_name"])}</span>
              <span class="meta">Z {fmt_num(top_bowler["Z_comp"], 3)} · Reliability {fmt_num(top_bowler["Reliability"], 1)}</span>
            </div>
            <div class="hero-stat">
              <span class="label">Sensitivity programme</span>
              <span class="name">{completed} completed runs</span>
              <span class="meta">{approved} approved · 10 supplementary diagnostics</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_grid(
        [
            ("Matches", f"{int(primary['matches']):,}", "Completed non-Super-Over", True),
            ("Deliveries", f"{int(primary['corpus_rows']):,}", "Approved scoring corpus", False),
            ("Eligible batters", f"{batter_eligible}", "F non-empty · M_role ≥ 10", True),
            ("Eligible bowlers", f"{bowler_eligible}", "F non-empty · M_role ≥ 10", True),
            ("Dual-role players", f"{dual_role}", "Eligible in both rankings", False),
            (
                "Sensitivity runs",
                f"{completed}",
                f"{approved} approved incl. primary · 20 approved alternatives",
                False,
            ),
        ]
    )

    left, right = st.columns([1.18, 0.82], gap="large")
    with left:
        _plot(eligibility_chart(data))
        st.caption(
            "The funnel separates the full player universe, the reliability calibration "
            "population, and the final ranking-eligible population for each role."
        )
    with right:
        st.markdown(
            panel(
                "What this dashboard answers",
                "<p>Who performs best under pressure, how reliable is each estimate, "
                "what does the format-level record look like, and how sensitive is the "
                "ranking to the approved measurement and eligibility alternatives?</p>"
                "<p>Scores are read directly from <code>outputs/stage5</code> and "
                "<code>outputs/stage6</code>. Nothing is recalculated, rescaled or "
                "re-ranked.</p>",
                "accent-border",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            panel(
                "Approved method at a glance",
                kv_rows(
                    [
                        ("Pressure cutoff", "P ≥ 60 · weight (P/100)²"),
                        ("Shrinkage", "K = 50"),
                        ("Gates", "N_raw ≥ 75 · N_eff ≥ 35"),
                        ("Match breadth", "M_role ≥ 10"),
                        ("Composite weights", "30 / 25 / 20 / 15 / 10"),
                        ("Reliability", "100 / (1 + exp(−0.80·Z_std))"),
                    ]
                ),
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            panel(
                "Headline caveat",
                "<p>The ranking is robust to the approved parameter grid, but not "
                "season-invariant. Under the 2024–2026 window, top-10 membership falls "
                "to 3/10 for batters and 4/10 for bowlers. These results are shown in "
                "Ranking Comparison, not suppressed.</p>",
                "amber-border",
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="margin:0.4rem 0 0.7rem 0">{badge("Stage 5 validation: 70 / 70 checks", "green")} '
        f'{badge("Stage 6 validation: 23 / 23 checks", "green")} '
        f'{badge("Stage 1–6 tests: 47 / 47", "green")}</div>',
        unsafe_allow_html=True,
    )

    section_heading("Primary top 10 snapshot", "Rank and scores displayed exactly as approved")
    tabs = st.tabs(["Batters", "Bowlers"])
    for tab, role in zip(tabs, ("batter", "bowler")):
        with tab:
            st.dataframe(
                top10_display(data[f"top10_{role}"]),
                hide_index=True,
                width="stretch",
                column_config=top10_column_config(),
                height=390,
            )
            st.caption(
                f"Source: outputs/stage5/top10_{role}s.csv. Filtering is available on the "
                "dedicated top-10 page and never changes the approved order."
            )

    section_heading("Explore the dashboard", "Four views, one approved evidence base")
    st.markdown(
        """
        <div class="insight-grid">
          <div class="insight-card">
            <h4>Top 10 rankings</h4>
            <p>Search, filter and re-sort the approved batter and bowler top 10 without changing ranks or scores.</p>
            <span class="where">Top 10 Batters · Top 10 Bowlers</span>
          </div>
          <div class="insight-card">
            <h4>Player profiles</h4>
            <p>Compare pressure with the player's personal baseline, inspect format scores, and see reliability against the eligible population.</p>
            <span class="where">Player Analysis</span>
          </div>
          <div class="insight-card">
            <h4>Ranking stability</h4>
            <p>Switch between approved scenarios, inspect membership turnover, and read the season-sensitivity caveat directly.</p>
            <span class="where">Ranking Comparison</span>
          </div>
          <div class="insight-card">
            <h4>Method and validation</h4>
            <p>Review coverage, eligibility gates, approved weights, calibration constants, limitations and all 23 Stage 6 checks.</p>
            <span class="where">Data and Methodology</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Top 10
# ---------------------------------------------------------------------------


def render_top10(data: dict[str, pd.DataFrame], role: str) -> None:
    label = ROLE_LABELS[role]
    top10 = data[f"top10_{role}"]
    page_header(
        "Primary rankings",
        f"Top 10 {label}s",
        "Approved Stage 5 rankings under pressure. Search, filter by eligible format, "
        "or re-sort the table without changing the underlying ranks or scores.",
        tags=[("Stage 5 approved", "green"), ("Display-only filters", "blue")],
    )

    top3 = top10.sort_values("final_rank").head(3)
    st.markdown(
        '<div class="podium-grid">'
        + "".join(
            _podium_card(row, int(row["final_rank"]))
            for _, row in top3.iterrows()
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "The podium always reflects the approved top three; table filters do not change it."
    )

    with st.container(border=True):
        controls = st.columns(
            [2.2, 1.05, 1.4, 0.72], vertical_alignment="bottom"
        )
        with controls[0]:
            query = st.text_input(
                "Search player or ID",
                placeholder="e.g. Mark Chapman or 3374",
                key=f"top10_query_{role}",
                icon=":material/search:",
            )
        with controls[1]:
            format_filter = st.selectbox(
                "Eligible format",
                ["All formats", "IPL", "T20I"],
                key=f"top10_format_{role}",
            )
        with controls[2]:
            sort_label = st.selectbox(
                "Sort by",
                [
                    "Final rank",
                    "Reliability (high to low)",
                    "Composite score (high to low)",
                    "Match count (high to low)",
                    "Player name (A-Z)",
                ],
                key=f"top10_sort_{role}",
            )
        with controls[3]:
            st.button(
                "Clear filters",
                key=f"top10_clear_{role}",
                width="stretch",
                on_click=_clear_top10_filters,
                args=(role,),
            )

    view = top10_view(top10, query, format_filter, sort_label)
    if view.empty:
        st.info("No top-10 player matches the current search and format filter.")
        return

    st.caption(
        f"{len(view)} of 10 approved players shown · sort: {sort_label} · "
        f"format: {format_filter}"
    )
    st.dataframe(
        top10_display(view),
        hide_index=True,
        width="stretch",
        column_config=top10_column_config(),
        height=390,
    )
    st.caption(
        f"Source: outputs/stage5/top10_{role}s.csv. Filtering and sorting are display-only; "
        "the approved rank order and scores are unchanged."
    )

    left, right = st.columns([1.48, 0.52], gap="large")
    with left:
        _plot(top10_bar(view, role))
        st.caption(
            "Bars show the approved composite score. The top three use the brighter accent; "
            "hover reveals reliability, formats and match count."
        )
    with right:
        st.markdown(
            panel(
                "How to read this",
                "<p><b>Composite Z</b> is the approved pressure-adjusted performance score. "
                "<b>Reliability</b> is a calibrated 0–100 precision index, not a probability.</p>"
                "<p><b>Matches</b> is M_role, the number of eligible matches in the player's "
                "qualifying formats. <b>N_raw</b> and <b>N_eff</b> describe pressure exposure before and "
                "after the Kish effective-sample adjustment.</p>"
                "<p>The top-10 list is fixed by the approved ranking. Filters only change "
                "which approved players are displayed.</p>",
            ),
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download filtered table (CSV)",
            data=top10_display(view).to_csv(index=False).encode("utf-8"),
            file_name=f"top10_{role}s_filtered.csv",
            mime="text/csv",
            width="stretch",
            key=f"download_top10_{role}",
            icon=":material/download:",
        )

    with st.expander("Approved ranking fields — audit view", expanded=False):
        display = top10_display(view)
        display.insert(8, "Z_std", view["Z_std"].to_numpy())
        st.dataframe(
            display,
            hide_index=True,
            width="stretch",
            column_config={
                **top10_column_config(),
                "Z_std": st.column_config.NumberColumn(format="%.4f"),
            },
            height=390,
        )
        st.caption(
            "Z_std is the standardized composite from the approved Stage 5 scoring file. "
            "It is shown for audit only and does not alter the ranking."
        )


# ---------------------------------------------------------------------------
# Player analysis
# ---------------------------------------------------------------------------


def _player_option_label(row: pd.Series) -> str:
    roles = " / ".join(ROLE_LABELS.get(role, role.title()) for role in row["roles"])
    rank = "" if pd.isna(row["best_rank"]) else f" · best rank {int(row['best_rank'])}"
    return f"{row['player_name']} · ID {int(row['player_id'])} · {roles}{rank}"


def render_player_analysis(data: dict[str, pd.DataFrame]) -> None:
    page_header(
        "Player profile",
        "Player Analysis",
        "Search by player name or ID. Inspect pressure versus baseline performance, "
        "format-level scores, reliability and sample size without recalculating anything.",
        tags=[("Read-only profile", "green"), ("Missing values shown as —", "")],
    )

    index = data["player_index"].copy()
    with st.container(border=True):
        search_col, select_col = st.columns([1.0, 1.55], vertical_alignment="bottom")
        with search_col:
            query = st.text_input(
                "Search player by name or player ID",
                placeholder="e.g. 3374, Mark Chapman, Moeen Ali",
                key="player_search",
                icon=":material/search:",
            )
        pool = index
        if query.strip():
            needle = query.strip().lower()
            pool = pool[pool["search"].str.contains(needle, regex=False)]
        if pool.empty:
            st.warning("No player matches that search. Try a player name or numeric ID.")
            return

        pool = pool.sort_values(["best_rank", "player_name"], na_position="last")
        option_ids = pool["player_id"].astype(int).tolist()
        option_map = {int(row["player_id"]): row for _, row in pool.iterrows()}
        with select_col:
            selected_id = st.selectbox(
                "Select player",
                options=option_ids,
                format_func=lambda player_id: _player_option_label(
                    option_map[int(player_id)]
                ),
                key="player_select",
            )
        selected = option_map[int(selected_id)]
        roles = list(selected["roles"])
        if len(roles) > 1:
            role = st.radio(
                "Role view",
                options=roles,
                format_func=lambda value: ROLE_LABELS.get(value, value.title()),
                horizontal=True,
                key="player_role",
            )
        else:
            role = roles[0]

    scoring_rows = data[f"{role}_scoring"]
    scoring = scoring_rows[scoring_rows["player_id"] == int(selected_id)].iloc[0]
    records = data[f"{role}_format"]
    records = records[records["player_id"] == int(selected_id)].copy()
    records = records.sort_values("format_label")

    other_roles = [value for value in roles if value != role]
    other_tags: list[tuple[str, str]] = []
    for other in other_roles:
        other_row = data[f"{other}_scoring"]
        other_row = other_row[other_row["player_id"] == int(selected_id)]
        if not other_row.empty and bool(other_row.iloc[0]["ranking_eligible"]):
            other_tags.append(
                (
                    f"{ROLE_LABELS[other]} rank {int(other_row.iloc[0]['final_rank'])}",
                    "blue",
                )
            )

    eligible = bool(scoring["ranking_eligible"])
    rank_text = f"Rank {int(scoring['final_rank'])}" if eligible else "Not ranked"
    header_tags = [
        (fmt_formats(scoring["F_formats"]), "green"),
        (ROLE_LABELS[role], ""),
        (rank_text, "green" if eligible else "amber"),
    ] + other_tags
    st.markdown(
        f"""
        <div class="player-hero">
          <div>
            <div class="player-kicker">{esc(ROLE_LABELS[role])} profile</div>
            <h2>{esc(scoring["player_name"])}</h2>
            <div class="player-meta">Player ID {int(selected_id)} · {esc(ROLE_LABELS[role])} view</div>
            {tag_row(header_tags)}
          </div>
          <div class="player-hero-score">
            <span>Composite Z</span>
            <strong>{fmt_num(scoring["Z_comp"], 4)}</strong>
            <em>{esc(rank_text)} · Reliability {fmt_num(scoring["Reliability"], 1)}</em>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not eligible:
        st.info(
            f"Not in the primary {ROLE_LABELS[role].lower()} ranking. "
            f"Status: {fmt_status(scoring['status'])}. "
            f"Detail: {fmt_text(scoring['exclusion_detail'])}."
        )

    metric_grid(
        [
            (
                "Final rank",
                fmt_int(scoring["final_rank"]) if eligible else "—",
                "Primary ranking",
                eligible,
            ),
            ("Composite Z", fmt_num(scoring["Z_comp"], 4), "Pressure-adjusted", False),
            ("Reliability", fmt_num(scoring["Reliability"], 1), "Calibrated 0–100", False),
            ("M_role", fmt_int(scoring["M_role"]), "Eligible matches", False),
            ("N_raw", fmt_int(scoring["sum_N_raw_F"]), "Pressure deliveries", False),
            ("N_eff", fmt_num(scoring["sum_N_eff_del_F"], 1), "Effective sample", False),
        ]
    )

    tabs = st.tabs(
        [
            "Pressure vs baseline",
            "Format scores",
            "Reliability & sample",
            "Detailed records",
        ]
    )

    with tabs[0]:
        chart = pressure_chart(records, role)
        if chart is None:
            st.info(
                "No format record passes the approved 120-ball personal-baseline gate. "
                "Pressure metrics are still shown in the table below."
            )
        else:
            _plot(chart)
            st.caption(
                "Each panel compares the player's personal baseline with the approved "
                "P ≥ 60 pressure set. Baseline values require at least 120 balls of exposure."
            )
        metric_columns = {
            "batter": [
                ("Format", "format_label"),
                ("Baseline SR", "SR_base"),
                ("Pressure SR", "SR_P"),
                ("Baseline dot %", "Dot_base"),
                ("Pressure dot %", "Dot_P"),
                ("Baseline DR", "DR_base"),
                ("Pressure DR", "DR_P"),
                ("Pressure boundary %", "Boundary_P"),
            ],
            "bowler": [
                ("Format", "format_label"),
                ("Baseline economy", "Econ_base"),
                ("Pressure economy", "Econ_P"),
                ("Baseline dot %", "Dot_base"),
                ("Pressure dot %", "Dot_bowl_P"),
                ("Baseline boundary %", "BoundaryConc_base"),
                ("Pressure boundary %", "BoundaryConc_P"),
                ("Pressure wicket rate", "WktRate_P"),
            ],
        }[role]
        display = records[[column for _, column in metric_columns]].rename(
            columns={column: label for label, column in metric_columns}
        )
        st.dataframe(
            display,
            hide_index=True,
            width="stretch",
            column_config={
                label: st.column_config.NumberColumn(format="%.2f")
                for label, column in metric_columns
                if column != "format_label"
            },
        )

    with tabs[1]:
        chart = format_score_chart(records, role)
        if chart is None:
            st.info("No format record passes the format composite gate for this player.")
        else:
            _plot(chart)
            st.caption(
                "Format Z is the approved format-level composite. The primary player "
                "score is the equal-weight mean across eligible formats."
            )
        display = records[
            [
                "format_label",
                "N_raw",
                "N_eff_del",
                "M_format",
                "baseline_ok",
                "format_gate",
                "Z_comp_format",
                "record_status",
            ]
        ].copy()
        display["Baseline gate"] = np.where(records["baseline_ok"], "Pass", "Not met")
        display["Format gate"] = np.where(records["format_gate"], "Pass", "Not met")
        display = display.drop(columns=["baseline_ok", "format_gate"]).rename(
            columns={
                "format_label": "Format",
                "N_raw": "N_raw",
                "N_eff_del": "N_eff",
                "M_format": "Matches",
                "Z_comp_format": "Format Z",
                "record_status": "Record status",
            }
        )
        st.dataframe(
            display,
            hide_index=True,
            width="stretch",
            column_config={
                "N_raw": st.column_config.NumberColumn(format="%d"),
                "N_eff": st.column_config.NumberColumn(format="%.1f"),
                "Matches": st.column_config.NumberColumn(format="%d"),
                "Format Z": st.column_config.NumberColumn(format="%.4f"),
            },
        )

    with tabs[2]:
        _plot(reliability_chart(data[f"{role}_scoring"], int(selected_id), role))
        st.caption(
            "The star marks this player against every ranking-eligible player in the role. "
            "Higher reliability means a more precisely estimated composite, not a better player."
        )
        metric_grid(
            [
                ("Z_std", fmt_num(scoring["Z_std"], 4), "Standardized composite", False),
                ("M_all", fmt_int(scoring["M_all"]), "All-format matches", False),
                (
                    "Format records",
                    f"{int(records['composite_ready'].sum())}",
                    "Composite-ready",
                    False,
                ),
                (
                    "Baseline records",
                    f"{int(records['baseline_ok'].sum())}",
                    "120-ball gate passed",
                    False,
                ),
            ]
        )
        st.markdown(
            r"""
            **Reliability formula**

            $$Reliability = \frac{100}{1 + \exp(-0.80\,Z_{std})}$$

            Reliability is a calibrated 0–100 index, not a probability of selection.
            It is centred at 50 at the calibration mean. The replacement level is 50.
            """
        )

    with tabs[3]:
        detail = records[
            [
                "format_label",
                "M_format",
                "N_raw",
                "N_eff_del",
                "baseline_ok",
                "format_gate",
                "Z_comp_format",
                "record_status",
            ]
        ].copy()
        detail["Baseline gate"] = np.where(records["baseline_ok"], "Pass", "Not met")
        detail["Format gate"] = np.where(records["format_gate"], "Pass", "Not met")
        detail = detail.drop(columns=["baseline_ok", "format_gate"]).rename(
            columns={
                "format_label": "Format",
                "M_format": "Matches",
                "N_raw": "N_raw",
                "N_eff_del": "N_eff",
                "Z_comp_format": "Format Z",
                "record_status": "Record status",
            }
        )
        st.dataframe(
            detail,
            hide_index=True,
            width="stretch",
            column_config={
                "Matches": st.column_config.NumberColumn(format="%d"),
                "N_raw": st.column_config.NumberColumn(format="%d"),
                "N_eff": st.column_config.NumberColumn(format="%.1f"),
                "Format Z": st.column_config.NumberColumn(format="%.4f"),
            },
        )
        st.download_button(
            "Download full approved record (CSV)",
            data=records.to_csv(index=False).encode("utf-8"),
            file_name=f"{role}_{int(selected_id)}_format_records.csv",
            mime="text/csv",
            key="download_player_records",
            icon=":material/download:",
        )
        st.caption(
            "The download contains every approved Stage 5 format-record column for this "
            "player-role. The table above shows the fields needed to read the score."
        )


# ---------------------------------------------------------------------------
# Ranking comparison
# ---------------------------------------------------------------------------


def render_ranking_comparison(data: dict[str, pd.DataFrame]) -> None:
    page_header(
        "Sensitivity analytics",
        "Ranking Comparison",
        "Compare primary ranks with every approved Stage 6 scenario. Spearman and "
        "top-10 membership are calculated on the common eligible population.",
        tags=[("Approved scenarios first", "green"), ("Supplementary opt-in", "blue")],
    )

    summary = data["sensitivity_summary"].copy()
    include_supplementary = bool(
        st.session_state.get("include_supplementary", False)
    )
    completed_statuses = (
        ["PRIMARY", "COMPLETED", "COMPLETED_SUPPLEMENTARY"]
        if include_supplementary
        else ["PRIMARY", "COMPLETED"]
    )
    completed = summary[
        summary["status"].isin(completed_statuses)
    ].copy()

    category_options = [
        ("all", "All completed scenarios"),
        ("baseline", "Primary baseline"),
        ("approved_grid", "Approved grid"),
        ("approved_mandatory", "Approved mandatory"),
    ]
    if include_supplementary:
        category_options.append(
            ("supplementary_non_approved", "Supplementary — diagnostic")
        )

    with st.container(border=True):
        controls = st.columns([1.0, 1.7], vertical_alignment="bottom")
        with controls[0]:
            category_choice = st.selectbox(
                "Scenario group",
                options=[key for key, _ in category_options],
                format_func=lambda key: dict(category_options)[key],
                key="comparison_category",
            )
        if category_choice == "all":
            selectable = completed.copy()
        else:
            selectable = completed[completed["category"] == category_choice].copy()
        if selectable.empty:
            st.error("No sensitivity scenarios are available in this group.")
            return
        scenario_ids = selectable["scenario_id"].tolist()
        default_scenario = "P_65" if "P_65" in scenario_ids else scenario_ids[0]
        with controls[1]:
            selected = st.selectbox(
                "Sensitivity scenario",
                options=scenario_ids,
                index=scenario_ids.index(default_scenario),
                format_func=lambda value: (
                    f"{value} · {format_category(selectable.loc[selectable['scenario_id'] == value, 'category'].iloc[0])}"
                ),
                key="comparison_scenario",
            )

    row = summary[summary["scenario_id"] == selected].iloc[0]
    approved = bool(row["approved"])
    st.markdown(
        f"""
        <div class="scenario-panel">
          <div class="scenario-title">
            {badge("Approved scenario" if approved else "Supplementary — not approved methodology", "green" if approved else "amber")}
            <strong>{esc(selected)}</strong>
            {tag(format_category(row["category"]), "blue" if approved else "")}
          </div>
          <p>{esc(row["description"])}</p>
          <p><b>Change from primary:</b> {esc(fmt_text(row["change_from_primary"]))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Scenario parameters", expanded=False):
        parameters = fmt_text(row["parameters"])
        if parameters == "—":
            st.caption("No parameter record is registered for this scenario.")
        else:
            st.code(parameters, language=None)

    for role in ("batter", "bowler"):
        section_heading(
            f"{ROLE_LABELS[role]} ranking",
            "Common eligible population",
        )
        metric_grid(
            [
                (
                    "Eligible",
                    fmt_int(row[f"{role}_eligible_count"]),
                    f"primary {fmt_int(row[f'{role}_primary_eligible_count'])}",
                    True,
                ),
                (
                    "Top-10 overlap",
                    f"{int(row[f'{role}_top10_overlap'])}/10",
                    f"Jaccard {fmt_num(row[f'{role}_top10_jaccard'], 3)}",
                    False,
                ),
                (
                    "Spearman ρ",
                    fmt_num(row[f"{role}_spearman"], 4),
                    "target > 0.92",
                    False,
                ),
            ]
        )

    role_tabs = st.tabs(["Batter detail", "Bowler detail"])
    for tab, role in zip(role_tabs, ("batter", "bowler")):
        with tab:
            metric_grid(
                [
                    (
                        "Kendall τ",
                        fmt_num(row[f"{role}_kendall"], 4),
                        "common population",
                        False,
                    ),
                    (
                        "Common n",
                        fmt_int(row[f"{role}_common_n"]),
                        "eligible in both",
                        False,
                    ),
                    (
                        "Mean |Δrank|",
                        fmt_num(row[f"{role}_mean_abs_rank_change"], 2),
                        "common players",
                        False,
                    ),
                    (
                        "Max |Δrank|",
                        fmt_num(row[f"{role}_max_abs_rank_change"], 1),
                        "common players",
                        False,
                    ),
                    (
                        "Entrants / leavers",
                        f"{int(row[f'{role}_entrants'])} / {int(row[f'{role}_leavers'])}",
                        "top-10 membership",
                        False,
                    ),
                ]
            )

            comparison = _comparison_table(data, role, selected)
            section_heading(
                "Top-10 membership and rank movement",
                "Retained · entrant · leaver",
            )
            if comparison.empty:
                st.info("No top-10 membership comparison is available for this scenario.")
            else:
                display = comparison[
                    [
                        "Primary rank",
                        "Scenario rank",
                        "player_name",
                        "player_id",
                        "Membership",
                        "Z_comp",
                        "Reliability",
                        "Delta rank",
                    ]
                ].copy()
                display["Movement"] = display["Delta rank"].map(
                    lambda value: fmt_signed(value, 1)
                )
                display = display.rename(
                    columns={
                        "player_name": "Player",
                        "player_id": "Player ID",
                        "Z_comp": "Scenario Z",
                        "Reliability": "Scenario Reliability",
                    }
                )[
                    [
                        "Primary rank",
                        "Scenario rank",
                        "Movement",
                        "Player",
                        "Player ID",
                        "Membership",
                        "Scenario Z",
                        "Scenario Reliability",
                    ]
                ]
                st.dataframe(
                    display,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Primary rank": st.column_config.NumberColumn(format="%d"),
                        "Scenario rank": st.column_config.NumberColumn(format="%d"),
                        "Movement": st.column_config.TextColumn(width="small"),
                        "Player ID": st.column_config.NumberColumn(format="%d"),
                        "Scenario Z": st.column_config.NumberColumn(format="%.4f"),
                        "Scenario Reliability": st.column_config.NumberColumn(
                            format="%.1f"
                        ),
                    },
                )
                st.download_button(
                    f"Download {role} movement table (CSV)",
                    data=display.to_csv(index=False).encode("utf-8"),
                    file_name=f"{role}_{selected}_movement.csv",
                    mime="text/csv",
                    key=f"download_comparison_{role}",
                    icon=":material/download:",
                )
                chart = scenario_bump_chart(comparison, selected, role)
                _plot(chart)
                st.caption(
                    "Retained = in both top 10s. Entrant = new in the scenario top 10. "
                    "Leaver = primary top-10 player outside the scenario top 10. "
                    "Players outside a top 10 are drawn on the Outside 10 row."
                )

            section_heading(
                "Stable and sensitive primary top-10 players",
                "Approved scenarios only · at least 10 comparisons",
            )
            stable, sensitive = _movement_tables(data, role)
            stable_col, sensitive_col = st.columns(2, gap="large")
            table_config = {
                "Rank": st.column_config.NumberColumn(format="%d"),
                "Top-10 appearances": st.column_config.TextColumn(),
                "Mean |Δrank|": st.column_config.NumberColumn(format="%.2f"),
                "Max |Δrank|": st.column_config.NumberColumn(format="%.1f"),
                "Mean |ΔZ|": st.column_config.NumberColumn(format="%.4f"),
            }
            with stable_col:
                st.markdown("**Most stable** · lowest mean |Δrank|")
                st.dataframe(
                    _movement_display(stable),
                    hide_index=True,
                    width="stretch",
                    column_config=table_config,
                )
            with sensitive_col:
                st.markdown("**Most sensitive** · highest mean |Δrank|")
                st.dataframe(
                    _movement_display(sensitive),
                    hide_index=True,
                    width="stretch",
                    column_config=table_config,
                )
            st.caption(
                "Individual rank movements can be larger than top-10 membership turnover. "
                "A retained player can move several places."
            )

            section_heading(
                "Scenarios in this view — Spearman correlation",
                "Bars below the dotted line (approved ρ 0.92 target) indicate weaker stability",
            )
            _plot(scenario_correlation_chart(summary, role, scenario_ids))
            below = summary[
                summary["scenario_id"].isin(scenario_ids)
                & (summary["approved"] == True)  # noqa: E712
                & (pd.to_numeric(summary[f"{role}_spearman"], errors="coerce") <= 0.92)
            ]
            st.caption(
                f"{len(below)} approved scenario(s) in this view fall at or below the "
                "0.92 target. Season-equal and 2024–2026-only scenarios change the "
                "evidence population and are expected to be less stable."
            )

    if not include_supplementary:
        st.info(
            "Supplementary diagnostics are hidden. Enable **Include supplementary "
            "scenarios** in the sidebar to inspect the non-approved σ, h, leverage and "
            "wide-stumping variants."
        )
    blocked = summary[
        ~summary["status"].isin(
            ["PRIMARY", "COMPLETED", "COMPLETED_SUPPLEMENTARY"]
        )
    ]
    if not blocked.empty:
        st.caption(
            "Not run: "
            + "; ".join(
                f"{fmt_text(row['scenario_id'])} ({fmt_text(row['status'])})"
                for _, row in blocked.iterrows()
            )
            + ". Both are explicitly labelled in the Stage 6 outputs."
        )


# ---------------------------------------------------------------------------
# Data and methodology
# ---------------------------------------------------------------------------


def render_data_methodology(data: dict[str, pd.DataFrame]) -> None:
    page_header(
        "Reference",
        "Data and Methodology",
        "Coverage, eligibility, approved scoring rules, reliability calibration, "
        "validation evidence, and the limitations that must travel with the rankings.",
        tags=[("Approved methodology", "green"), ("Validation evidence", "blue")],
    )

    summary = data["sensitivity_summary"]
    primary = summary[summary["scenario_id"] == "PRIMARY"].iloc[0]
    checks = data["validation_checks"]
    passed_checks = int(checks["passed"].fillna(False).astype(bool).sum())

    tabs = st.tabs(
        [
            "Coverage",
            "Eligibility",
            "Scoring",
            "Reliability",
            "Limitations",
            "Validation",
        ]
    )

    with tabs[0]:
        metric_grid(
            [
                (
                    "Matches",
                    f"{int(primary['matches']):,}",
                    "Scoring corpus",
                    True,
                ),
                (
                    "Deliveries",
                    f"{int(primary['corpus_rows']):,}",
                    "Completed non-Super-Over",
                    False,
                ),
                (
                    "Audit deliveries",
                    "192,056",
                    "Includes 93 Match 48610 chase rows",
                    False,
                ),
                ("T20 / IPL", "87,217", "Deliveries", False),
                ("T20I", "104,746", "Deliveries", False),
                ("other extras", "256", "Provisional classification", False),
            ]
        )
        coverage = pd.DataFrame(
            [
                ("Scoring matches", "812", "completed non-Super-Over matches"),
                ("Scoring deliveries", "191,963", "approved pressure/feature corpus"),
                (
                    "Audit deliveries",
                    "192,056",
                    "includes the 93 excluded Match 48610 chase rows",
                ),
                ("T20 / IPL deliveries", "87,217", "format-level coverage"),
                ("T20I deliveries", "104,746", "format-level coverage"),
                (
                    "Match 48610 retained",
                    "101",
                    "first-innings deliveries retained",
                ),
                (
                    "Match 48610 excluded",
                    "93",
                    "second-innings chase rows excluded",
                ),
                (
                    "other extras",
                    "256",
                    "scoring corpus; classification unresolved",
                ),
            ],
            columns=["Quantity", "Value", "Note"],
        )
        st.dataframe(coverage, hide_index=True, width="stretch")
        st.caption(
            "The scoring corpus is the approved 191,963-delivery completed non-Super-Over "
            "file after the Q9 Match 48610 exclusion. The 192,056-row audit corpus is "
            "retained for reconciliation."
        )
        st.markdown(
            panel(
                "Why two corpora?",
                "<p>The audit corpus is the full cleaned delivery file used for "
                "reconciliation. The scoring corpus removes the 93 unresolved "
                "second-innings rows from Match 48610. Every Stage 5 metric and every "
                "Stage 6 scenario is computed from the approved scoring corpus, not "
                "from the dashboard.</p>",
                "accent-border",
            ),
            unsafe_allow_html=True,
        )

    with tabs[1]:
        st.markdown(
            """
            <div class="step-grid">
              <div class="step-card">
                <div class="step-num">STEP 01</div>
                <h4>Format set F</h4>
                <p>A role is considered only when the format set F is non-empty. Players and roles outside F are excluded.</p>
              </div>
              <div class="step-card">
                <div class="step-num">STEP 02</div>
                <h4>Exposure gates</h4>
                <p>Pressure cutoff P ≥ 60, raw gate N_raw ≥ 75 pressure deliveries, and effective gate N_eff ≥ 35.</p>
              </div>
              <div class="step-card">
                <div class="step-num">STEP 03</div>
                <h4>Baseline gate</h4>
                <p>Batter baselines need 120 balls faced or 120 legal balls by metric. Bowler baselines need 120 legal balls.</p>
              </div>
              <div class="step-card">
                <div class="step-num">STEP 04</div>
                <h4>Final population</h4>
                <p>The final M_role gate is 10 eligible matches. The calibration population deliberately does not apply that gate.</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        counts = []
        for role in ("batter", "bowler"):
            scoring = data[f"{role}_scoring"]
            records = data[f"{role}_format"]
            counts.append(
                {
                    "Role": ROLE_LABELS[role],
                    "All player rows": len(scoring),
                    "F non-empty players": int(scoring["F_nonempty"].sum()),
                    "Calibration n": int(scoring["calibration_population"].sum()),
                    "Composite-ready records": int(records["composite_ready"].sum()),
                    "Final records": int(records["ranking_eligible"].sum()),
                    "Final eligible players": int(scoring["ranking_eligible"].sum()),
                }
            )
        st.dataframe(pd.DataFrame(counts), hide_index=True, width="stretch")
        dual = len(
            set(
                data["batter_scoring"].loc[
                    data["batter_scoring"]["ranking_eligible"], "player_id"
                ]
            )
            & set(
                data["bowler_scoring"].loc[
                    data["bowler_scoring"]["ranking_eligible"], "player_id"
                ]
            )
        )
        st.info(
            f"{dual} players are eligible in both role rankings. Batter and bowler "
            "rankings remain separate; there is no combined all-rounder primary ranking."
        )

    with tabs[2]:
        st.markdown(
            "**Approved composite weights and signs** · identical 30 / 25 / 20 / 15 / 10 "
            "structure for both roles"
        )
        weight_rows = [
            ("Batter", "ΔSR", "30%", "positive"),
            ("Batter", "SR_P", "25%", "positive"),
            ("Batter", "Boundary%_P", "20%", "positive"),
            ("Batter", "ΔDot%", "15%", "positive"),
            ("Batter", "ΔDR", "10%", "positive"),
            ("Bowler", "ΔEcon", "30%", "positive"),
            ("Bowler", "Econ_P", "25%", "negative"),
            ("Bowler", "WktRate_P", "20%", "positive"),
            ("Bowler", "Dot%_bowl,P", "15%", "positive"),
            ("Bowler", "BoundaryConc_P", "10%", "negative"),
        ]
        rows_html = "".join(
            f"<tr><td>{esc(role)}</td><td>{esc(metric)}</td>"
            f'<td class="num">{esc(weight)}</td><td>{esc(sign)}</td></tr>'
            for role, metric, weight, sign in weight_rows
        )
        st.markdown(
            '<div class="table-scroll"><table class="data-table">'
            "<thead><tr><th>Role</th><th>Metric</th><th>Weight</th><th>Sign</th></tr></thead>"
            f"<tbody>{rows_html}</tbody></table></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            panel(
                "From raw metric to composite",
                "<p>Each metric is shrunk toward an approved peer mean with K = 50, then "
                "standardized against approved format-specific reference moments. The "
                "format composite is the weighted sum of the five standardized terms. "
                "The player composite is the equal-weight mean across the formats in F.</p>"
                "<p>Pressure P is situational and is not itself a performance score. "
                "Batter and bowler engines use different state variables and link "
                "functions.</p>",
                "accent-border",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            "**Ranking order and tie-breaks**\n\n"
            "1. Composite Z descending.\n"
            "2. Summed N_eff,del over eligible formats descending.\n"
            "3. M_role descending.\n"
            "4. Summed N_raw over eligible formats descending.\n"
            "5. Player ID ascending.\n\n"
            "The primary method uses equal cross-format weighting. N_eff-proportional "
            "weighting is an approved sensitivity, not the primary. Capped N_eff "
            "weighting is optional and was not run because no numeric cap C is approved."
        )

    with tabs[3]:
        st.markdown(
            r"""
            ### Reliability

            $$Z_{std} = \frac{Z_{comp} - \mu_{Zcomp}}{\sigma_{Zcomp}}$$

            $$Reliability = \frac{100}{1 + \exp(-0.80\,Z_{std})}$$

            Reliability is centred at 50 at the calibration mean. It is a calibrated
            precision index, not a probability that a player will be selected or will
            perform well.
            """
        )
        calibration = pd.DataFrame(
            [
                ("Batter", "122", "0.1036068081", "0.6610638828"),
                ("Bowler", "173", "0.0256919707", "0.6655792246"),
            ],
            columns=["Role", "Calibration n", "μ_Zcomp", "σ_Zcomp"],
        )
        st.dataframe(calibration, hide_index=True, width="stretch")
        st.caption(
            "Approved calibration values are fixed and are not re-estimated by this dashboard."
        )
        st.markdown(
            panel(
                "Reading reliability correctly",
                "<p>Reliability describes how precisely the composite is estimated on the "
                "approved calibration population. A high value does not mean a player is "
                "better; a low value does not mean a player is worse. It answers a "
                "different question from Composite Z.</p>",
            ),
            unsafe_allow_html=True,
        )

    with tabs[4]:
        limitations = [
            (
                "PROVISIONAL_OTHER",
                "The cricket meaning of other extras is unresolved. The primary bowler "
                "boundary-conceded treatment is the provisional all-extras rule "
                "(9,816 scoring / 9,827 audit), not a fully verified classification.",
            ),
            (
                "Match 48610 DLS provenance",
                "The DLS provenance of Match 48610 remains unresolved. The 93 "
                "second-innings rows are excluded from pressure and personal baselines; "
                "the P1 fallback is a sensitivity/audit device only.",
            ),
            (
                "Correlation pair identities",
                "The historical correlation values 0.4778, 0.5233 and -0.692 are retained, "
                "but their exact metric pairs are not reconstructed. No independence claim "
                "is made.",
            ),
            (
                "Season stability",
                "Season-equal and 2024–2026-only sensitivities produce lower rank "
                "correlations than the approved parameter grid. The ranking is not "
                "season-invariant; this is disclosed, not suppressed.",
            ),
            (
                "Wide-stumping asymmetry",
                "25 wide stumpings are retained in the wicket-rate numerator, but only 6 "
                "are in the bowler pressure set. The legal-ball denominator is unchanged.",
            ),
            (
                "Retire Out",
                "Retire Out exclusion is proposed and documented but not fully "
                "source-verified across every scorecard.",
            ),
            (
                "Derived bowler runs",
                "bowler_runs is derived as batter runs plus wide/overstep/other extras; "
                "byes, leg-byes and penalties are not charged to the bowler.",
            ),
            (
                "No combined all-rounder ranking",
                "Batter and bowler rankings are independent. An all-rounder may appear in "
                "both, but there is no combined all-rounder primary score.",
            ),
        ]
        cards = "".join(
            f'<div class="panel"><h4>{esc(title)}</h4>'
            f'<p>{esc(text)}</p></div>'
            for title, text in limitations
        )
        st.markdown(
            f'<div class="limitation-grid">{cards}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "These limitations are part of the approved project record. Improving the "
            "wording here does not change the underlying methodology."
        )

    with tabs[5]:
        metric_grid(
            [
                ("Stage 5 checks", "70 / 70", "PASS", True),
                (
                    "Stage 6 checks",
                    f"{passed_checks} / {len(checks)}",
                    "Independent validation",
                    True,
                ),
                ("Stage 1–6 tests", "47 / 47", "Existing project tests", False),
                ("Primary eligible", "101 / 141", "Batters / bowlers", False),
            ]
        )

        section_heading("Stage 6 validation log", f"{passed_checks} of {len(checks)} checks passed")
        display = checks.rename(
            columns={
                "area": "Area",
                "check": "Check",
                "passed": "Passed",
                "detail": "Detail",
            }
        )
        st.dataframe(
            display,
            hide_index=True,
            width="stretch",
            column_config={
                "Passed": st.column_config.CheckboxColumn(),
                "Detail": st.column_config.TextColumn(width="large"),
            },
            height=520,
        )
        st.caption(
            "The validation layer independently recomputed correlations, overlaps, "
            "eligibility changes and primary reproduction from the generated CSVs."
        )

        section_heading("Scenario register", "33 registered runs")
        registry = summary[
            [
                "scenario_id",
                "category",
                "status",
                "approved",
                "mandatory",
                "description",
            ]
        ].rename(
            columns={
                "scenario_id": "Scenario",
                "category": "Category",
                "status": "Status",
                "approved": "Approved",
                "mandatory": "Mandatory",
                "description": "Description",
            }
        )
        st.dataframe(
            registry,
            hide_index=True,
            width="stretch",
            column_config={
                "Approved": st.column_config.CheckboxColumn(),
                "Mandatory": st.column_config.CheckboxColumn(),
                "Description": st.column_config.TextColumn(width="large"),
            },
            height=430,
        )
        st.caption(
            "21 approved scenarios (primary plus 20 alternatives), 10 supplementary "
            "diagnostics, and two explicitly blocked/optional scenarios are registered."
        )


__all__ = [
    "render_data_methodology",
    "render_overview",
    "render_player_analysis",
    "render_ranking_comparison",
    "render_top10",
]
