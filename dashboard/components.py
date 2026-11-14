"""Reusable formatting and presentation components for the SupeRR dashboard."""

from __future__ import annotations

import html
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import streamlit as st

from theme import CATEGORY_LABELS, COLORS


def esc(value: object) -> str:
    """Escape a value for safe insertion into custom HTML."""
    return html.escape(str(value), quote=True)


def fmt_num(value: object, digits: int = 3, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not np.isfinite(number):
        return "—"
    return f"{number:,.{digits}f}{suffix}"


def fmt_int(value: object) -> str:
    if value is None or pd.isna(value):
        return "—"
    try:
        return f"{int(round(float(value))):,}"
    except (TypeError, ValueError):
        return str(value)


def fmt_text(value: object) -> str:
    if value is None or pd.isna(value):
        return "—"
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "<na>"}:
        return "—"
    return text


def fmt_formats(value: object) -> str:
    text = fmt_text(value)
    if text == "—":
        return text
    return text.replace(",", " + ")


def fmt_signed(value: object, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    if not np.isfinite(number):
        return "—"
    return f"{number:+,.{digits}f}"


def fmt_status(value: object) -> str:
    text = fmt_text(value)
    if text == "—":
        return text
    return text.replace("_", " ").title()


def format_category(category: str) -> str:
    return CATEGORY_LABELS.get(category, str(category).replace("_", " ").title())


def metric_card_html(
    label: str, value: object, sub: str = "", accent: bool = False
) -> str:
    klass = "metric-card accent" if accent else "metric-card"
    return (
        f'<div class="{klass}">'
        f'<div class="metric-label">{esc(label)}</div>'
        f'<div class="metric-value">{esc(value)}</div>'
        f'<div class="metric-sub">{esc(sub)}</div>'
        "</div>"
    )


def metric_grid(cards: Iterable[Sequence[object]]) -> None:
    """Render a responsive grid of metric cards.

    Each card is ``(label, value, sub, accent)``; a three-item tuple is also
    accepted and treated as non-accented.
    """
    html_cards: list[str] = []
    for card in cards:
        label, value = card[0], card[1]
        sub = card[2] if len(card) > 2 else ""
        accent = bool(card[3]) if len(card) > 3 else False
        html_cards.append(metric_card_html(str(label), value, str(sub), accent))
    st.markdown(
        '<div class="metric-grid six">' + "".join(html_cards) + "</div>"
        if len(html_cards) == 6
        else '<div class="metric-grid">' + "".join(html_cards) + "</div>",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: object, sub: str = "", accent: bool = False) -> None:
    """Backward-compatible single-card wrapper."""
    metric_grid([(label, value, sub, accent)])


def section_heading(title: str, note: str = "") -> None:
    st.markdown(
        f'<div class="section-heading"><h3>{esc(title)}</h3>'
        f"<span>{esc(note)}</span></div>",
        unsafe_allow_html=True,
    )


def page_header(
    kicker: str,
    title: str,
    subtitle: str,
    tags: Sequence[tuple[str, str]] | None = None,
) -> None:
    tag_html = ""
    if tags:
        tag_html = '<div class="page-tags">' + "".join(
            f'<span class="tag {esc(kind)}">{esc(text)}</span>'
            for text, kind in tags
        ) + "</div>"
    st.markdown(
        f'<div class="page-header">'
        f'<div class="page-kicker">{esc(kicker)}</div>'
        f"<h1>{esc(title)}</h1>"
        f'<p class="page-subtitle">{esc(subtitle)}</p>'
        f"{tag_html}</div>",
        unsafe_allow_html=True,
    )


def badge(text: str, kind: str = "green") -> str:
    klass = {
        "green": "status-badge",
        "amber": "status-badge amber",
        "red": "status-badge red",
    }.get(kind, "status-badge")
    return f'<span class="{klass}"><span class="dot"></span>{esc(text)}</span>'


def tag(text: str, kind: str = "") -> str:
    klass = f"tag {kind}".strip()
    return f'<span class="{klass}">{esc(text)}</span>'


def tag_row(tags: Sequence[tuple[str, str]]) -> str:
    return '<div class="tag-row">' + "".join(
        tag(text, kind) for text, kind in tags
    ) + "</div>"


def panel(title: str, body_html: str, extra_class: str = "") -> str:
    klass = f"panel {extra_class}".strip()
    return (
        f'<div class="{klass}"><h4>{esc(title)}</h4>{body_html}</div>'
    )


def kv_rows(rows: Sequence[tuple[str, str]]) -> str:
    return "".join(
        f'<div class="kv"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>'
        for label, value in rows
    )


def player_tag(role: str, rank: float | None = None) -> str:
    label = role.title() if role else "Player"
    if rank is not None and not pd.isna(rank):
        return tag(f"{label} rank {int(rank)}", "green")
    return tag(label, "blue")


def empty_table_message(message: str) -> None:
    st.info(message, icon=":material/info:")


def style_numeric(value: float, digits: int = 3) -> str:
    return fmt_num(value, digits)


__all__ = [
    "COLORS",
    "badge",
    "empty_table_message",
    "esc",
    "fmt_formats",
    "fmt_int",
    "fmt_num",
    "fmt_signed",
    "fmt_status",
    "fmt_text",
    "format_category",
    "kv_rows",
    "metric_card",
    "metric_card_html",
    "metric_grid",
    "page_header",
    "panel",
    "player_tag",
    "section_heading",
    "tag",
    "tag_row",
]
