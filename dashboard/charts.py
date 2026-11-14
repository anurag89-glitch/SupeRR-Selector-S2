"""Plotly chart builders for the SupeRR dashboard.

Every chart visualises approved values from the Stage 5 and Stage 6 CSV
outputs.  No score, rank, correlation or eligibility value is recomputed here.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from components import esc, fmt_num, fmt_signed
from theme import (
    CATEGORY_COLORS,
    CATEGORY_LABELS,
    COLORS,
    MEMBERSHIP_COLORS,
    PLOTLY_TEMPLATE,
)

ROLE_LABELS = {"batter": "Batter", "bowler": "Bowler"}


def style_figure(
    fig: go.Figure,
    height: int = 420,
    *,
    show_legend: bool = True,
    margin: dict[str, int] | None = None,
) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Segoe UI, Inter, sans-serif",
            color=COLORS["text"],
            size=12,
        ),
        margin=margin or dict(l=8, r=18, t=54, b=38),
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="#0f243b",
            bordercolor=COLORS["green"],
            font=dict(color=COLORS["text"], size=12),
        ),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.11,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10),
        ),
    )
    fig.update_xaxes(
        gridcolor="rgba(148,163,184,0.11)",
        zerolinecolor="rgba(148,163,184,0.16)",
        linecolor="rgba(148,163,184,0.16)",
        tickfont=dict(size=11),
        title_font=dict(size=11, color=COLORS["muted"]),
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.11)",
        zerolinecolor="rgba(148,163,184,0.16)",
        linecolor="rgba(148,163,184,0.16)",
        tickfont=dict(size=11),
        title_font=dict(size=11, color=COLORS["muted"]),
        automargin=True,
    )
    return fig


def top10_bar(top10: pd.DataFrame, role: str) -> go.Figure:
    table = top10.sort_values("final_rank").copy()
    labels = [
        f"#{int(row.final_rank)}  {row.player_name}" for row in table.itertuples()
    ]
    colors = [
        COLORS["green_bright"] if int(rank) <= 3 else COLORS["green_dark"]
        for rank in table["final_rank"]
    ]
    fig = go.Figure(
        go.Bar(
            x=table["Z_comp"],
            y=labels,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[fmt_num(value, 3) for value in table["Z_comp"]],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=10, color=COLORS["muted"]),
            customdata=np.stack(
                [
                    table["final_rank"],
                    table["F_formats"].map(lambda v: str(v).replace(",", " + ")),
                    table["M_role"],
                    table["Reliability"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Composite Z %{x:.4f}<br>"
                "Reliability %{customdata[3]:.2f}<br>"
                "Formats %{customdata[1]} · Matches %{customdata[2]}"
                "<extra></extra>"
            ),
        )
    )
    values = pd.to_numeric(table["Z_comp"], errors="coerce").dropna()
    low = min(0.0, float(values.min()))
    high = max(0.0, float(values.max()))
    pad = max((high - low) * 0.16, 0.05)
    fig.update_layout(
        title=dict(
            text=f"Top 10 {ROLE_LABELS[role]}s — Composite Score",
            font=dict(size=15),
            x=0.01,
            xanchor="left",
        ),
        xaxis_title="Composite Z (approved pressure-adjusted score)",
        yaxis_title="",
    )
    fig.update_xaxes(range=[low - (pad if low < 0 else 0), high + pad])
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=11))
    return style_figure(fig, 420, show_legend=False, margin=dict(l=8, r=36, t=54, b=38))


def eligibility_chart(data: dict[str, pd.DataFrame]) -> go.Figure:
    labels: list[str] = []
    universe: list[int] = []
    calibration: list[int] = []
    eligible: list[int] = []
    for role in ("batter", "bowler"):
        scoring = data[f"{role}_scoring"]
        labels.append(f"{ROLE_LABELS[role]}s")
        universe.append(len(scoring))
        calibration.append(int(scoring["calibration_population"].sum()))
        eligible.append(int(scoring["ranking_eligible"].sum()))

    fig = go.Figure()
    series = [
        ("All player rows", universe, "#334155"),
        ("Calibration population", calibration, COLORS["green_dark"]),
        ("Final ranking eligible", eligible, COLORS["green_bright"]),
    ]
    for name, values, color in series:
        fig.add_trace(
            go.Bar(
                name=name,
                x=labels,
                y=values,
                marker_color=color,
                marker_line_width=0,
                text=[f"{value:,}" for value in values],
                textposition="outside",
                cliponaxis=False,
                textfont=dict(size=10, color=COLORS["muted"]),
                hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:,}}<extra></extra>",
            )
        )
    top = max(max(universe), max(calibration), max(eligible))
    fig.update_layout(
        barmode="group",
        bargap=0.3,
        bargroupgap=0.08,
        title=dict(
            text="Eligibility funnel by role",
            font=dict(size=15),
            x=0.01,
            xanchor="left",
        ),
        yaxis_title="Players",
        xaxis_title="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=1,
            xanchor="right",
        ),
    )
    fig.update_yaxes(rangemode="tozero", range=[0, top * 1.18])
    return style_figure(fig, 380, show_legend=True, margin=dict(l=8, r=18, t=58, b=56))


def pressure_chart(records: pd.DataFrame, role: str) -> go.Figure | None:
    table = records[records["baseline_ok"]].copy()
    if table.empty:
        return None

    if role == "batter":
        metrics = [
            ("Strike rate", "SR_base", "SR_P", 1),
            ("Dot ball %", "Dot_base", "Dot_P", 1),
            ("Dismissal rate", "DR_base", "DR_P", 2),
        ]
    else:
        metrics = [
            ("Economy", "Econ_base", "Econ_P", 2),
            ("Dot ball %", "Dot_base", "Dot_bowl_P", 1),
            ("Boundary conceded %", "BoundaryConc_base", "BoundaryConc_P", 1),
        ]

    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=[f"<b>{metric[0]}</b>" for metric in metrics],
        vertical_spacing=0.12,
    )
    for index, (title, base_col, pressure_col, digits) in enumerate(metrics, start=1):
        for series_name, column, color in (
            ("Personal baseline", base_col, "#94a3b8"),
            ("Pressure (P ≥ 60)", pressure_col, COLORS["green"]),
        ):
            values = pd.to_numeric(table[column], errors="coerce")
            fig.add_trace(
                go.Bar(
                    x=table["format_label"],
                    y=values,
                    name=series_name,
                    legendgroup=series_name,
                    marker_color=color,
                    marker_line_width=0,
                    text=[fmt_num(value, digits) for value in values],
                    textposition="outside",
                    cliponaxis=False,
                    textfont=dict(size=10, color=COLORS["muted"]),
                    showlegend=index == 1,
                    hovertemplate=(
                        f"<b>{series_name} · {title}</b><br>"
                        "%{x}: %{y:,.2f}<extra></extra>"
                    ),
                ),
                row=index,
                col=1,
            )
    fig.update_layout(
        barmode="group",
        bargap=0.3,
        bargroupgap=0.06,
        title=dict(
            text=f"Pressure versus personal baseline — {ROLE_LABELS[role]}",
            font=dict(size=15),
            x=0.01,
            xanchor="left",
        ),
    )
    fig.update_annotations(
        font=dict(size=12, color=COLORS["muted"]),
        x=0.0,
        xanchor="left",
    )
    fig.update_yaxes(rangemode="tozero")
    return style_figure(fig, 560, show_legend=True, margin=dict(l=8, r=18, t=64, b=70))


def format_score_chart(records: pd.DataFrame, role: str) -> go.Figure | None:
    table = records[records["composite_ready"]].copy()
    table = table[pd.to_numeric(table["Z_comp_format"], errors="coerce").notna()]
    if table.empty:
        return None
    table = table.sort_values("format_label")
    colors = [
        COLORS["green"] if float(value) >= 0 else COLORS["red"]
        for value in table["Z_comp_format"]
    ]
    fig = go.Figure(
        go.Bar(
            x=table["format_label"],
            y=table["Z_comp_format"],
            marker_color=colors,
            marker_line_width=0,
            text=[fmt_num(value, 3) for value in table["Z_comp_format"]],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=10, color=COLORS["muted"]),
            customdata=np.stack(
                [table["N_raw"], table["N_eff_del"], table["M_format"]], axis=-1
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Format composite %{y:.4f}<br>"
                "N_raw %{customdata[0]:,.0f} · N_eff %{customdata[1]:,.1f}<br>"
                "Matches %{customdata[2]:,.0f}<extra></extra>"
            ),
        )
    )
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(230,238,248,0.25)")
    fig.update_layout(
        title=dict(
            text=f"Format-specific composite — {ROLE_LABELS[role]}",
            font=dict(size=15),
            x=0.01,
            xanchor="left",
        ),
        xaxis_title="",
        yaxis_title="Format Z",
    )
    return style_figure(fig, 320, show_legend=False, margin=dict(l=8, r=18, t=54, b=38))


def reliability_chart(scoring: pd.DataFrame, player_id: int, role: str) -> go.Figure:
    table = scoring[scoring["ranking_eligible"]].copy()
    table = table[
        pd.to_numeric(table["sum_N_eff_del_F"], errors="coerce").notna()
        & pd.to_numeric(table["Reliability"], errors="coerce").notna()
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=table["sum_N_eff_del_F"],
            y=table["Reliability"],
            mode="markers",
            name="Eligible players",
            marker=dict(
                color=COLORS["green"], size=6, opacity=0.38, line=dict(width=0)
            ),
            text=table["player_name"],
            customdata=np.stack([table["final_rank"], table["M_role"]], axis=-1),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Reliability %{y:.2f}<br>"
                "N_eff %{x:,.1f} · Rank %{customdata[0]:,.0f}"
                "<extra></extra>"
            ),
        )
    )
    selected = table[table["player_id"] == player_id]
    if not selected.empty:
        fig.add_trace(
            go.Scatter(
                x=selected["sum_N_eff_del_F"],
                y=selected["Reliability"],
                mode="markers",
                name="Selected player",
                marker=dict(
                    color=COLORS["amber"],
                    size=15,
                    symbol="star",
                    line=dict(color="#fff4cf", width=1),
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Reliability %{y:.2f}<br>N_eff %{x:,.1f}<extra></extra>"
                ),
                text=selected["player_name"],
            )
        )
    fig.add_hline(
        y=50,
        line_dash="dot",
        line_color="rgba(244,184,96,0.55)",
        annotation_text="Replacement level = 50",
        annotation_position="bottom right",
        annotation_font_color=COLORS["amber"],
    )
    fig.update_layout(
        title=dict(
            text=f"Reliability versus effective sample — {ROLE_LABELS[role]}",
            font=dict(size=15),
            x=0.01,
            xanchor="left",
        ),
        xaxis_title="Σ N_eff,del over eligible formats",
        yaxis_title="Reliability (0–100)",
    )
    max_x = float(pd.to_numeric(table["sum_N_eff_del_F"], errors="coerce").max())
    fig.update_xaxes(range=[0, max_x * 1.06])
    fig.update_yaxes(range=[0, 100])
    return style_figure(fig, 380, show_legend=True, margin=dict(l=8, r=18, t=58, b=78))


def scenario_bump_chart(
    comparison: pd.DataFrame, scenario_id: str, role: str
) -> go.Figure | None:
    table = comparison.copy()
    if table.empty:
        return None

    floor = 11.4
    primary_pos = (
        pd.to_numeric(table["primary_rank"], errors="coerce")
        .fillna(floor)
        .clip(upper=floor)
    )
    scenario_pos = (
        pd.to_numeric(table["final_rank"], errors="coerce")
        .fillna(floor)
        .clip(upper=floor)
    )

    fig = go.Figure()
    for (_, row), start, end in zip(table.iterrows(), primary_pos, scenario_pos):
        membership = row["Membership"]
        color = MEMBERSHIP_COLORS.get(membership, COLORS["slate"])
        primary_text = (
            "Outside top 10" if start >= floor else f"Rank {int(start)}"
        )
        scenario_text = (
            "Outside top 10" if end >= floor else f"Rank {int(end)}"
        )
        fig.add_trace(
            go.Scatter(
                x=["Primary", "Scenario"],
                y=[start, end],
                mode="lines+markers",
                showlegend=False,
                line=dict(color=color, width=1.8),
                marker=dict(
                    size=7,
                    color=color,
                    line=dict(color=COLORS["bg"], width=1),
                ),
                opacity=0.85,
                hovertemplate=(
                    f"<b>{esc(row['player_name'])}</b><br>"
                    f"Primary: {primary_text}<br>"
                    f"Scenario: {scenario_text}<br>"
                    f"Membership: {esc(membership)} · Change "
                    f"{fmt_signed(row['Delta rank'])}<extra></extra>"
                ),
            )
        )

    for label, color in MEMBERSHIP_COLORS.items():
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color=color, width=3),
                name=label,
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        title=dict(
            text=f"Top-10 rank movement — {ROLE_LABELS[role]}",
            font=dict(size=15),
            x=0.01,
            xanchor="left",
        ),
        xaxis_title="",
        yaxis_title="Rank",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=1,
            xanchor="right",
        ),
    )
    fig.update_xaxes(
        tickvals=["Primary", "Scenario"],
        range=[-0.35, 1.35],
    )
    fig.update_yaxes(
        autorange="reversed",
        tickmode="array",
        tickvals=list(range(1, 11)) + [floor],
        ticktext=[str(value) for value in range(1, 11)] + ["Outside 10"],
        range=[11.9, 0.35],
    )
    return style_figure(
        fig, 430, show_legend=True, margin=dict(l=8, r=25, t=62, b=64)
    )


def scenario_correlation_chart(
    summary: pd.DataFrame, role: str, scenario_ids: Iterable[str]
) -> go.Figure:
    table = summary[summary["scenario_id"].isin(list(scenario_ids))].copy()
    table = table[pd.to_numeric(table[f"{role}_spearman"], errors="coerce").notna()]
    table = table.sort_values(f"{role}_spearman")
    colors = [
        CATEGORY_COLORS.get(category, COLORS["slate"])
        for category in table["category"]
    ]
    fig = go.Figure(
        go.Bar(
            x=table[f"{role}_spearman"],
            y=table["scenario_id"],
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            showlegend=False,
            text=[fmt_num(value, 3) for value in table[f"{role}_spearman"]],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=10, color=COLORS["muted"]),
            customdata=np.stack(
                [
                    table[f"{role}_top10_overlap"],
                    table[f"{role}_eligible_count"],
                    table["category"].map(
                        lambda value: CATEGORY_LABELS.get(
                            value, str(value).replace("_", " ").title()
                        )
                    ),
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Spearman ρ %{x:.4f}<br>"
                "Top-10 overlap %{customdata[0]:,.0f}/10<br>"
                "Eligible %{customdata[1]:,.0f}<br>"
                "%{customdata[2]}<extra></extra>"
            ),
        )
    )

    for category, label in (
        ("baseline", "Primary"),
        ("approved_grid", "Approved grid"),
        ("approved_mandatory", "Mandatory"),
        ("supplementary_non_approved", "Supplementary"),
    ):
        if category not in set(table["category"]):
            continue
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(color=CATEGORY_COLORS[category], size=9),
                name=label,
                hoverinfo="skip",
            )
        )

    fig.add_vline(
        x=0.92,
        line_dash="dash",
        line_color=COLORS["amber"],
    )
    values = pd.to_numeric(table[f"{role}_spearman"], errors="coerce")
    low = max(0.60, float(values.min()) - 0.04)
    fig.update_layout(
        title=dict(
            text=f"Spearman correlation by scenario — {ROLE_LABELS[role]}",
            font=dict(size=15),
            x=0.01,
            xanchor="left",
        ),
        xaxis_title="Spearman ρ (common eligible population)",
        yaxis_title="",
        xaxis_range=[low, 1.02],
    )
    return style_figure(
        fig,
        max(430, 24 * len(table)),
        show_legend=True,
        margin=dict(l=8, r=46, t=60, b=84),
    )


__all__ = [
    "eligibility_chart",
    "format_score_chart",
    "pressure_chart",
    "reliability_chart",
    "scenario_bump_chart",
    "scenario_correlation_chart",
    "style_figure",
    "top10_bar",
]
