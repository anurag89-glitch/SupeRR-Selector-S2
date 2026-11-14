"""Visual design tokens and global styles for the SupeRR dashboard."""

from __future__ import annotations

COLORS = {
    "bg": "#060f1a",
    "panel": "#0d1c2f",
    "panel_2": "#11243a",
    "border": "rgba(148, 163, 184, 0.16)",
    "border_strong": "rgba(94, 234, 212, 0.28)",
    "text": "#e8eff8",
    "muted": "#9db0c5",
    "dim": "#7b8fa6",
    "green": "#2dd4a3",
    "green_bright": "#5eead4",
    "green_dark": "#1f8f72",
    "green_soft": "rgba(45, 212, 163, 0.08)",
    "amber": "#f4b860",
    "red": "#f87185",
    "blue": "#62a8f5",
    "slate": "#64748b",
}

PLOTLY_TEMPLATE = "plotly_dark"

CATEGORY_LABELS = {
    "baseline": "Primary baseline",
    "approved_grid": "Approved grid",
    "approved_mandatory": "Approved mandatory",
    "supplementary_non_approved": "Supplementary — not approved",
    "optional": "Optional — not run",
    "blocked": "Blocked — not approved",
}

CATEGORY_COLORS = {
    "baseline": COLORS["green_bright"],
    "approved_grid": COLORS["green"],
    "approved_mandatory": COLORS["blue"],
    "supplementary_non_approved": COLORS["slate"],
    "optional": COLORS["slate"],
    "blocked": COLORS["slate"],
}

MEMBERSHIP_COLORS = {
    "Retained": COLORS["green"],
    "Entrant": COLORS["blue"],
    "Leaver": COLORS["red"],
}


CSS = """
<style>
    :root {
        --sr-bg: #060f1a;
        --sr-panel: #0d1c2f;
        --sr-panel-2: #11243a;
        --sr-border: rgba(148, 163, 184, 0.16);
        --sr-text: #e8eff8;
        --sr-muted: #9db0c5;
        --sr-dim: #7b8fa6;
        --sr-green: #2dd4a3;
        --sr-green-bright: #5eead4;
        --sr-green-soft: rgba(45, 212, 163, 0.08);
        --sr-amber: #f4b860;
        --sr-red: #f87185;
        --sr-blue: #62a8f5;
        --sr-radius: 14px;
        --sr-shadow: 0 1px 2px rgba(0, 0, 0, 0.28), 0 10px 28px rgba(0, 0, 0, 0.16);
    }
    html, body, [class*="css"] {
        font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    }
    .stApp {
        background: linear-gradient(180deg, #081422 0%, #060f1a 360px);
        color: var(--sr-text);
    }
    [data-testid="stAppViewContainer"] { background: transparent; }
    .block-container {
        max-width: 1320px;
        padding: 1.4rem 2rem 3rem;
    }
    header[data-testid="stHeader"] {
        background: rgba(6, 15, 26, 0.55);
        backdrop-filter: blur(6px);
    }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stSidebar"] {
        background: #07121f;
        border-right: 1px solid var(--sr-border);
    }
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"] { padding-top: 0.65rem; }
    h1, h2, h3, h4 {
        letter-spacing: -0.015em;
        color: var(--sr-text);
        font-weight: 700;
    }
    p, li, label, span { color: var(--sr-text); }
    a { color: var(--sr-green-bright); }
    code {
        background: rgba(148, 163, 184, 0.1);
        color: #d7f7ee;
        padding: 0.08rem 0.3rem;
        border-radius: 5px;
        font-size: 0.85em;
    }

    /* Hero */
    .hero {
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: minmax(0, 1.5fr) minmax(255px, 0.72fr);
        gap: 1.6rem;
        padding: 1.8rem 2rem;
        border: 1px solid rgba(45, 212, 163, 0.22);
        border-radius: 20px;
        background: linear-gradient(135deg, #0d2638 0%, #0a1a2b 58%, #0a2628 100%);
        box-shadow: var(--sr-shadow);
        margin-bottom: 1.2rem;
    }
    .hero::before {
        content: "";
        position: absolute;
        right: -6rem;
        top: -8rem;
        width: 20rem;
        height: 20rem;
        border-radius: 50%;
        border: 1px solid rgba(45, 212, 163, 0.14);
        box-shadow: 0 0 0 3.2rem rgba(45, 212, 163, 0.03), 0 0 0 6.4rem rgba(45, 212, 163, 0.02);
        pointer-events: none;
    }
    .hero-copy { position: relative; z-index: 1; }
    .hero-kicker {
        color: var(--sr-green-bright);
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    .hero h1 {
        font-size: clamp(2rem, 3.2vw, 2.9rem);
        line-height: 1.02;
        margin: 0.15rem 0 0.55rem 0;
        font-weight: 800;
    }
    .hero p {
        color: #c3d5e6;
        max-width: 58rem;
        font-size: 0.95rem;
        line-height: 1.6;
        margin: 0;
    }
    .hero-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 1rem; }
    .hero-aside {
        position: relative;
        z-index: 1;
        align-self: center;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 14px;
        background: rgba(6, 17, 30, 0.55);
        padding: 0.85rem 1rem;
    }
    .hero-aside-head {
        color: var(--sr-muted);
        font-size: 0.64rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .hero-stat { border-top: 1px solid rgba(148, 163, 184, 0.1); padding: 0.5rem 0; }
    .hero-stat:first-of-type { border-top: none; }
    .hero-stat .label {
        display: block;
        color: var(--sr-dim);
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .hero-stat .name {
        display: block;
        font-size: 0.88rem;
        font-weight: 650;
        line-height: 1.3;
        overflow-wrap: anywhere;
    }
    .hero-stat .meta {
        display: block;
        color: var(--sr-green-bright);
        font-size: 0.72rem;
        font-variant-numeric: tabular-nums;
    }

    /* Tags, badges and small labels */
    .tag {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        border: 1px solid var(--sr-border);
        background: rgba(148, 163, 184, 0.07);
        color: var(--sr-text);
        border-radius: 6px;
        padding: 0.2rem 0.5rem;
        font-size: 0.7rem;
        font-weight: 600;
        line-height: 1.2;
        white-space: nowrap;
    }
    .tag.green { border-color: rgba(45, 212, 163, 0.28); background: var(--sr-green-soft); color: #c9fff1; }
    .tag.blue { border-color: rgba(98, 168, 245, 0.28); background: rgba(98, 168, 245, 0.08); color: #d8e9ff; }
    .tag.amber { border-color: rgba(244, 184, 96, 0.28); background: rgba(244, 184, 96, 0.08); color: #ffedc9; }
    .tag.red { border-color: rgba(248, 113, 133, 0.28); background: rgba(248, 113, 133, 0.08); color: #ffd9df; }
    .tag-row { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.45rem; }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.42rem;
        border-radius: 6px;
        padding: 0.26rem 0.55rem;
        font-size: 0.7rem;
        font-weight: 700;
        border: 1px solid rgba(45, 212, 163, 0.28);
        background: var(--sr-green-soft);
        color: #c8fff0;
    }
    .status-badge.amber {
        border-color: rgba(244, 184, 96, 0.32);
        background: rgba(244, 184, 96, 0.08);
        color: #ffe6a8;
    }
    .status-badge.red {
        border-color: rgba(248, 113, 133, 0.32);
        background: rgba(248, 113, 133, 0.08);
        color: #ffd2d9;
    }
    .dot {
        width: 0.42rem;
        height: 0.42rem;
        border-radius: 50%;
        background: var(--sr-green-bright);
        display: inline-block;
        box-shadow: 0 0 0 3px rgba(45, 212, 163, 0.12);
    }
    .status-badge.amber .dot { background: var(--sr-amber); box-shadow: 0 0 0 3px rgba(244, 184, 96, 0.12); }
    .status-badge.red .dot { background: var(--sr-red); box-shadow: 0 0 0 3px rgba(248, 113, 133, 0.12); }

    /* Page and section headings */
    .page-header { margin: 0.15rem 0 1.05rem 0; }
    .page-kicker {
        color: var(--sr-green-bright);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    .page-header h1 {
        font-size: clamp(1.7rem, 2.6vw, 2.15rem);
        line-height: 1.1;
        margin: 0.05rem 0 0.35rem 0;
    }
    .page-subtitle {
        color: var(--sr-muted);
        font-size: 0.91rem;
        line-height: 1.55;
        max-width: 66rem;
        margin: 0;
    }
    .page-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.6rem; }
    .section-heading {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 1rem;
        margin: 1.45rem 0 0.65rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--sr-border);
    }
    .section-heading h3 { font-size: 1.02rem; margin: 0; }
    .section-heading span { color: var(--sr-dim); font-size: 0.74rem; }

    /* Metric cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(172px, 1fr));
        gap: 0.65rem;
        margin: 0.15rem 0 1.05rem 0;
    }
    .metric-grid.six {
        grid-template-columns: repeat(6, minmax(0, 1fr));
    }
    .metric-card {
        position: relative;
        overflow: hidden;
        min-height: 6.2rem;
        border: 1px solid var(--sr-border);
        border-radius: var(--sr-radius);
        padding: 0.85rem 0.95rem;
        background: var(--sr-panel);
        box-shadow: var(--sr-shadow);
    }
    .metric-card::after {
        content: "";
        position: absolute;
        left: 0;
        top: 14px;
        bottom: 14px;
        width: 2px;
        border-radius: 0 2px 2px 0;
        background: rgba(148, 163, 184, 0.25);
    }
    .metric-card.accent {
        border-color: rgba(45, 212, 163, 0.24);
        background: linear-gradient(180deg, rgba(45, 212, 163, 0.055), rgba(45, 212, 163, 0) 62%), var(--sr-panel);
    }
    .metric-card.accent::after { background: var(--sr-green); }
    .metric-label {
        color: var(--sr-muted);
        font-size: 0.65rem;
        font-weight: 800;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        margin-bottom: 0.32rem;
    }
    .metric-value {
        color: var(--sr-text);
        font-size: 1.5rem;
        line-height: 1.08;
        font-weight: 800;
        letter-spacing: -0.025em;
        font-variant-numeric: tabular-nums;
        overflow-wrap: anywhere;
    }
    .metric-sub {
        color: var(--sr-dim);
        font-size: 0.72rem;
        line-height: 1.4;
        margin-top: 0.32rem;
    }

    /* Panels and definition rows */
    .panel {
        border: 1px solid var(--sr-border);
        border-radius: var(--sr-radius);
        padding: 0.95rem 1.05rem;
        background: var(--sr-panel);
        box-shadow: var(--sr-shadow);
        margin-bottom: 0.65rem;
    }
    .panel h4 { font-size: 0.9rem; margin: 0 0 0.35rem 0; }
    .panel p {
        color: var(--sr-muted);
        font-size: 0.82rem;
        line-height: 1.55;
        margin: 0 0 0.4rem 0;
    }
    .panel p:last-child { margin-bottom: 0; }
    .panel strong { color: var(--sr-text); }
    .panel.accent-border { border-left: 2px solid var(--sr-green); }
    .panel.amber-border { border-left: 2px solid var(--sr-amber); }
    .panel.compact { padding: 0.75rem 0.9rem; }
    .kv {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 0.8rem;
        padding: 0.34rem 0;
        border-top: 1px solid rgba(148, 163, 184, 0.1);
        font-size: 0.78rem;
    }
    .kv:first-of-type { border-top: none; padding-top: 0.1rem; }
    .kv span { color: var(--sr-muted); }
    .kv strong { text-align: right; font-variant-numeric: tabular-nums; }

    /* Podium */
    .podium-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 0.65rem;
        margin: 0.15rem 0 1rem 0;
    }
    .podium-card {
        border: 1px solid var(--sr-border);
        border-radius: var(--sr-radius);
        padding: 0.9rem 1rem;
        background: var(--sr-panel);
        box-shadow: var(--sr-shadow);
    }
    .podium-card.rank-1 {
        border-color: rgba(45, 212, 163, 0.32);
        background: linear-gradient(160deg, rgba(45, 212, 163, 0.08), rgba(45, 212, 163, 0) 60%), var(--sr-panel);
    }
    .podium-rank {
        color: var(--sr-dim);
        font-size: 0.64rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .podium-card.rank-1 .podium-rank { color: var(--sr-green-bright); }
    .podium-name {
        font-size: 1rem;
        font-weight: 700;
        margin: 0.18rem 0 0.1rem 0;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }
    .podium-meta { color: var(--sr-muted); font-size: 0.72rem; }
    .podium-score {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 0.5rem;
        margin-top: 0.55rem;
        padding-top: 0.5rem;
        border-top: 1px solid rgba(148, 163, 184, 0.1);
    }
    .podium-score strong { font-size: 1.02rem; font-variant-numeric: tabular-nums; }
    .podium-score span { color: var(--sr-dim); font-size: 0.7rem; }

    /* Player header */
    .player-hero {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
        border: 1px solid var(--sr-border);
        border-radius: 16px;
        padding: 1.05rem 1.2rem;
        background: linear-gradient(140deg, #0e2235, #0b1a2b);
        box-shadow: var(--sr-shadow);
        margin: 0.2rem 0 0.9rem 0;
    }
    .player-hero h2 {
        margin: 0.08rem 0 0.12rem 0;
        font-size: 1.6rem;
        line-height: 1.1;
        overflow-wrap: anywhere;
    }
    .player-kicker {
        color: var(--sr-green);
        font-size: 0.64rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .player-meta { color: var(--sr-muted); font-size: 0.78rem; }
    .player-hero-score { text-align: right; flex-shrink: 0; }
    .player-hero-score span {
        display: block;
        color: var(--sr-muted);
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
    }
    .player-hero-score strong { font-size: 1.45rem; font-variant-numeric: tabular-nums; }
    .player-hero-score em {
        display: block;
        color: var(--sr-green-bright);
        font-style: normal;
        font-size: 0.73rem;
    }

    /* Steps and insight cards */
    .step-grid, .insight-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 0.65rem;
        margin: 0.35rem 0 1rem 0;
    }
    .step-card, .insight-card {
        border: 1px solid var(--sr-border);
        border-radius: 12px;
        background: var(--sr-panel);
        padding: 0.85rem 0.9rem;
    }
    .step-num {
        color: var(--sr-green);
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 0.12em;
    }
    .step-card h4, .insight-card h4 { font-size: 0.86rem; margin: 0.2rem 0 0.28rem 0; }
    .step-card p, .insight-card p {
        color: var(--sr-muted);
        font-size: 0.76rem;
        line-height: 1.5;
        margin: 0;
    }
    .insight-card .where {
        display: block;
        margin-top: 0.45rem;
        color: var(--sr-green);
        font-size: 0.68rem;
        font-weight: 700;
    }

    /* Scenario panel */
    .scenario-panel {
        border: 1px solid var(--sr-border);
        border-radius: var(--sr-radius);
        background: var(--sr-panel);
        padding: 0.85rem 1rem;
        margin: 0.2rem 0 0.9rem 0;
        box-shadow: var(--sr-shadow);
    }
    .scenario-title {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.55rem;
        margin-bottom: 0.25rem;
    }
    .scenario-title strong { font-size: 0.95rem; }
    .scenario-panel p {
        color: var(--sr-muted);
        font-size: 0.8rem;
        line-height: 1.5;
        margin: 0.15rem 0 0 0;
    }

    /* Data tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--sr-border);
        border-radius: 12px;
        overflow: hidden;
    }
    .table-scroll { overflow-x: auto; margin: 0.2rem 0 0.8rem 0; }
    table.data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.78rem;
        background: var(--sr-panel);
        border: 1px solid var(--sr-border);
        border-radius: 12px;
        overflow: hidden;
    }
    table.data-table th {
        text-align: left;
        padding: 0.55rem 0.65rem;
        color: var(--sr-muted);
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        background: rgba(148, 163, 184, 0.06);
        border-bottom: 1px solid var(--sr-border);
        white-space: nowrap;
    }
    table.data-table td {
        padding: 0.5rem 0.65rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.08);
        color: var(--sr-text);
        vertical-align: top;
    }
    table.data-table tr:last-child td { border-bottom: none; }
    table.data-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
    table.data-table code { font-size: 0.76rem; }

    /* Limitation cards */
    .limitation-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(265px, 1fr));
        gap: 0.65rem;
        margin-top: 0.4rem;
    }
    .limitation-grid .panel { margin-bottom: 0; }

    /* Sidebar */
    .sidebar-brand {
        border: 1px solid rgba(45, 212, 163, 0.2);
        background: linear-gradient(145deg, rgba(16, 52, 59, 0.55), rgba(8, 21, 35, 0.9));
        border-radius: 16px;
        padding: 0.9rem 0.95rem;
        margin-bottom: 0.9rem;
    }
    .sidebar-brand .mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.05rem;
        height: 2.05rem;
        border-radius: 10px;
        background: var(--sr-green);
        color: #052018;
        font-weight: 900;
        font-size: 0.75rem;
        letter-spacing: -0.04em;
        margin-bottom: 0.5rem;
    }
    .sidebar-brand h2 { font-size: 1.08rem; margin: 0; }
    .sidebar-brand p { color: var(--sr-muted); font-size: 0.72rem; margin: 0.2rem 0 0 0; line-height: 1.4; }
    .sidebar-section-label {
        margin: 0.9rem 0 0.3rem 0;
        color: var(--sr-dim);
        font-size: 0.6rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }
    .sidebar-status {
        border: 1px solid var(--sr-border);
        border-radius: 12px;
        padding: 0.65rem 0.75rem;
        background: rgba(13, 28, 47, 0.7);
        color: var(--sr-muted);
        font-size: 0.72rem;
        line-height: 1.5;
        margin: 0.35rem 0 0.7rem 0;
    }
    .status-row { display: flex; align-items: center; gap: 0.45rem; padding: 0.14rem 0; }
    [data-testid="stSidebar"] [role="radiogroup"] > label {
        padding: 0.28rem 0.45rem;
        border-radius: 7px;
        transition: background 120ms ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] > label:hover {
        background: rgba(45, 212, 163, 0.06);
    }

    /* Native controls */
    [data-baseweb="input"] { background: var(--sr-panel); }
    div[data-baseweb="select"] > div {
        background: var(--sr-panel);
        border-color: var(--sr-border);
    }
    .stButton button, .stDownloadButton button {
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        border-color: rgba(45, 212, 163, 0.5);
        color: var(--sr-green-bright);
    }
    button:focus-visible, input:focus-visible {
        outline: 2px solid rgba(45, 212, 163, 0.45);
        outline-offset: 1px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.2rem;
        border-bottom: 1px solid var(--sr-border);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.48rem 0.72rem;
        font-size: 0.82rem;
    }
    .stTabs [aria-selected="true"] { color: var(--sr-green-bright); }

    .footer {
        border-top: 1px solid var(--sr-border);
        color: #7e95ab;
        font-size: 0.74rem;
        padding-top: 0.9rem;
        margin-top: 1.8rem;
        line-height: 1.55;
    }

    @media (max-width: 1400px) {
        .metric-grid.six { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
    @media (max-width: 1100px) {
        .block-container { padding-left: 1.5rem; padding-right: 1.5rem; }
        .hero { grid-template-columns: 1fr; gap: 1rem; }
        .hero-aside { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.4rem; }
        .hero-aside-head { grid-column: 1 / -1; }
        .hero-stat { border-top: none; border-left: 1px solid rgba(148, 163, 184, 0.1); padding: 0.15rem 0 0.15rem 0.65rem; }
        .hero-stat:first-of-type { border-left: none; padding-left: 0; }
        [data-testid="stHorizontalBlock"] { flex-direction: column; gap: 0.9rem; }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 auto !important;
            min-width: 0 !important;
        }
    }
    @media (max-width: 1000px) {
        .metric-grid.six { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 760px) {
        .block-container { padding: 1rem 0.9rem 2rem; }
        .hero { padding: 1.3rem 1.1rem; border-radius: 16px; }
        .hero h1 { font-size: 1.9rem; }
        .hero-aside { grid-template-columns: 1fr; }
        .hero-stat { border-left: none; border-top: 1px solid rgba(148, 163, 184, 0.1); padding: 0.45rem 0; }
        .hero-stat:first-of-type { border-top: none; }
        .player-hero { flex-direction: column; align-items: flex-start; }
        .player-hero-score { text-align: left; }
        .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .metric-value { font-size: 1.32rem; }
        .podium-grid { grid-template-columns: 1fr; }
        .section-heading { align-items: flex-start; flex-direction: column; gap: 0.15rem; }
        .stTabs [data-baseweb="tab"] { padding: 0.45rem 0.55rem; font-size: 0.78rem; }
    }
    @media (max-width: 380px) {
        .metric-grid { grid-template-columns: 1fr; }
        .metric-grid.six { grid-template-columns: 1fr; }
        .hero-tags .tag { white-space: normal; }
    }
</style>
"""
