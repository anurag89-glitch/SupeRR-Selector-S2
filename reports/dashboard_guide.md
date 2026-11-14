# SupeRR Selector — Dashboard Usage Guide

## Purpose

The Stage 7 dashboard is a read-only presentation layer over the approved Stage 5 primary rankings and Stage 6 sensitivity outputs. It does **not** recalculate pressure, shrink metrics, calibrate reliability, rank players, or rerun sensitivity scenarios. It reads the approved CSVs and displays them.

Use it to answer four questions:

1. Who are the approved top-10 batters and bowlers?
2. What does an individual player's pressure-versus-baseline record look like?
3. How stable is a ranking under each approved Stage 6 scenario?
4. Which methodology rules and limitations travel with these results?

## Launch

From the project root, create a virtual environment and install the dashboard requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

Streamlit opens `http://localhost:8501` in the default browser. To choose another port or run without opening a browser:

```bash
python -m streamlit run dashboard/app.py --server.port 8507 --server.headless true
```

The app reads only the approved CSV outputs under `outputs/stage5` and `outputs/stage6`, resolved relative to the repository. Raw and processed datasets are not required, and no network connection is needed at runtime. `requirements.txt` pins the validated dashboard environment: Streamlit 1.67.0, pandas 3.1.1, NumPy 2.5.4 and Plotly 7.1.0. For Streamlit Community Cloud, set the main file path to `dashboard/app.py`.

`.streamlit/config.toml` applies the dark native theme and a minimal toolbar. It does not change any analytical value.

## Pages

### 1. Overview

- Read-only introduction and approved-method summary.
- Six KPI cards: 812 matches, 191,963 scoring deliveries, 101 eligible batters, 141 eligible bowlers, 23 dual-role players, and 31 completed sensitivity runs (21 approved including the primary, 10 supplementary diagnostics).
- Eligibility funnel separating the full player universe, calibration population, and final ranking-eligible population.
- Approved top-10 snapshots for both roles, with exact ranks and scores.
- Validation status: Stage 5 70/70 checks, Stage 6 23/23 checks, Stage 1–6 tests 47/47.

### 2. Top 10 Batters

- Podium for the approved top three; it does not change when the table is filtered.
- Search by player name or player ID.
- Filter to IPL or T20I eligibility.
- Re-sort by final rank, reliability, composite score, match count, or player name.
- Clear all controls with one button.
- Styled ranking table with per-column help text, followed by a composite-score chart.
- **Approved ranking fields — audit view** expands to the complete approved ranking record, including `Z_std` and the intermediate fields used by Stage 5.
- Download the currently filtered table as CSV.

Filtering and sorting are display-only. The approved ranks and scores are never changed, and the download contains only the displayed rows.

### 3. Top 10 Bowlers

Same structure and controls as the batter page, using the approved bowler ranking and bowler audit fields.

### 4. Player Analysis

- Search by player name or player ID, then select a player.
- For dual-role players, switch between batter and bowler views.
- Read final rank, composite Z, reliability, M_role, N_raw, and N_eff in a KPI grid.
- Inspect four tabs:
  - **Pressure vs baseline:** format-level pressure metrics against the player's personal baseline.
  - **Format scores:** approved format-specific composite scores.
  - **Reliability & sample:** the player's reliability against the full eligible population.
  - **Detailed records:** the complete approved format-record table.
- Download the full approved player record as CSV.

Missing or ineligible values are displayed as an em dash. The dashboard does not fabricate values for players outside the approved ranking population.

### 5. Ranking Comparison

- **Scenario group** scopes the selector to all approved scenarios, the primary baseline, the approved grid, or the approved mandatory alternatives. Enable **Include supplementary scenarios** in the sidebar to add all 31 completed runs and the supplementary diagnostic group.
- Select any completed scenario. The default is `P_65`.
- See scenario metadata, eligible counts, top-10 overlap, Jaccard, Spearman rho, Kendall tau, and mean/max absolute rank movement for batters and bowlers.
- Inspect retained players, entrants, leavers, and rank movement.
- Compare stable and sensitive primary top-10 players.
- View batter and bowler rank-movement (bump) charts and the Spearman correlation chart.
- Download either movement table as CSV.

Top-10 **membership turnover** and individual rank movement are distinct. A player can remain in the top 10 while moving several places. The comparison tables report both.

**Include supplementary scenarios** in the sidebar adds the 10 non-approved diagnostics. It never exposes them by default, and it never alters primary scores or ranks.

### 6. Data and Methodology

Tabs cover:

- **Coverage:** matches, deliveries, format split, Match 48610, and `other` extras.
- **Eligibility:** format gates and the final match-breadth gate.
- **Scoring:** approved weights, signs, shrinkage, standardization, and tie-breaks.
- **Reliability:** calibration constants and the logistic reliability formula.
- **Limitations:** `PROVISIONAL_OTHER`, Match 48610 DLS provenance, wide-stumping asymmetry, season stability, Retire Out, derived bowler runs, and the absence of a combined all-rounder ranking.
- **Validation:** Stage 5, Stage 6, and test-suite evidence, plus the full scenario register.

## Design and responsive behaviour

- Dark navy surfaces, teal/emerald accents, restrained borders, and a compact card system.
- Responsive KPI grids: six across above 1400 px, three columns at 1400 px and below, two columns at 1000 px and below, one column at 380 px and below.
- Streamlit horizontal blocks stack below 1100 px so charts, tables, and control groups keep usable widths.
- Plotly legends sit below the plot area, preventing title/legend collisions on narrow screens.
- Tables use Streamlit column formatting. Wide tables scroll inside their own container; the page itself does not overflow horizontally.
- Charts have hover details and no Plotly mode bar.
- The sidebar provides navigation, validation status, the supplementary-scenario toggle, and data-source/build details.
- Empty searches, missing values, ineligible players, and unavailable charts are handled with clear messages instead of crashing.

## Data sources

| Source | Used for |
| :--- | :--- |
| `outputs/stage5/batter_scoring.csv` | Batter ranks, composite, reliability, eligibility |
| `outputs/stage5/bowler_scoring.csv` | Bowler ranks, composite, reliability, eligibility |
| `outputs/stage5/batter_format_records.csv` | Batter format-level pressure and baseline records |
| `outputs/stage5/bowler_format_records.csv` | Bowler format-level pressure and baseline records |
| `outputs/stage5/top10_batters.csv` | Approved batter top 10 |
| `outputs/stage5/top10_bowlers.csv` | Approved bowler top 10 |
| `outputs/stage6/sensitivity_summary.csv` | Scenario register, correlations, overlaps, eligibility |
| `outputs/stage6/batter_sensitivity_rankings.csv` | Batter scenario ranks |
| `outputs/stage6/bowler_sensitivity_rankings.csv` | Bowler scenario ranks |
| `outputs/stage6/batter_top10_stability.csv` | Batter membership and movement detail |
| `outputs/stage6/bowler_top10_stability.csv` | Bowler membership and movement detail |
| `outputs/stage6/player_rank_changes.csv` | Stable/sensitive player summaries |
| `outputs/stage6/eligibility_sensitivity.csv` | Eligibility changes by scenario |
| `outputs/stage6/scenario_diagnostics.csv` | Scenario corpus and pressure diagnostics |
| `outputs/stage6/stage6_validation_checks.csv` | 23 independent Stage 6 checks |

The dashboard loads these files directly. It does not write to them.

## Validation performed

- **Test suite:** 61/61 tests passing — 47 approved Stage 1–6 tests plus 14 dashboard regression tests in `tests/test_dashboard.py`.
- **Page rendering:** all six pages rendered through Streamlit `AppTest` with zero exceptions and the expected structural counts (Overview 2 tables/1 chart; each Top 10 page 2/1; Player Analysis 3/3; Ranking Comparison 6/4; Data and Methodology 5/0).
- **Approved rankings:** displayed top-10 order, player IDs, composite scores, reliability, and effective sample sizes match `outputs/stage5/top10_*.csv`; the audit view exposes `Z_std` at the approved precision.
- **Approved scenarios:** all 31 completed scenarios render without exceptions; Stage 6 ranks, scores, reliability, overlap, and correlation values are compared with the approved CSVs, and the 23/23 Stage 6 checks are displayed unchanged.
- **Interactions:** searches, ID lookup, role switching, format filters, all sort options, clear controls, empty and non-matching searches, supplementary-scenario toggling, scenario-group scoping, and all download controls are covered.
- **Charts:** chart builders were exercised for all 242 ranked batter/bowler profiles and every completed scenario with finite construction.
- **Headless health:** Streamlit served the app on `127.0.0.1:8511`; `/_stcore/health` returned HTTP 200 (`ok`).
- **Responsive browser check:** all six pages were driven through headless Chrome DevTools at 1440×1000, 834×1112, and 390×844. No page-level horizontal overflow and no JavaScript console errors were observed. The mobile sidebar started collapsed, opened, closed, and left the content unobstructed. Key page sections were manually reviewed in screenshots at each viewport; this is not a golden-image pixel-diff suite.
- **Protected-file integrity:** a pre-work SHA-256 snapshot of 80 protected files (data, Stage 5/6 outputs, `src`, Stage 1–6 tests, and Stage 4.2/5/6 reports) was recomputed after the work. **80/80 hashes are unchanged**, with no missing files.

## Known limitations

- **Season sensitivity:** `SEASON_EQUAL` and `SEASON_2024_2026` fall below the approved `rho > 0.92` target. The primary ranking is not season-invariant. The dashboard discloses this rather than suppressing it.
- **Top-10 turnover:** A top-10 overlap of 6/10 or 7/10 means four or three members changed, not that all players moved by that many places. Individual rank movements can be larger.
- **`PROVISIONAL_OTHER`:** The cricket meaning of `other` extras remains unresolved. The primary bowler boundary-conceded treatment is the provisional all-extras rule.
- **Match 48610:** The DLS provenance remains unresolved. The 93 second-innings chase rows are excluded from primary pressure and baselines; the P1 fallback is a sensitivity/audit device only.
- **No combined all-rounder score:** Batter and bowler rankings are independent. The 23 dual-role players appear in both where eligible, but no combined ranking exists.
- **Display precision:** Scores are formatted for readability; the approved CSVs remain the authoritative record.
- **Runtime:** The dashboard depends on the approved CSV files being present. If an output is missing, the app stops with a clear error instead of substituting values.
- **Narrow-screen tables:** Wide tables scroll horizontally inside their card. This is intentional and does not cause page-level overflow.

## Troubleshooting

| Symptom | Check |
| :--- | :--- |
| `ModuleNotFoundError: streamlit` | Run with `.\venv\Scripts\python.exe`, not a global Python install. |
| Port already in use | Add `--server.port 8507` or another free port. |
| Missing required approved outputs | Confirm the `outputs/stage5` and `outputs/stage6` CSVs exist. |
| Table appears filtered | Use **Clear filters** on the top-10 page or clear the Player Analysis search. |
| Supplementary scenarios absent | Enable **Include supplementary scenarios** in the sidebar. |
| Chart legend or table looks cramped | Resize wider; columns stack and legends move below plots on narrow screens by design. |

## Guardrails

Do not edit the source CSVs from the dashboard. Do not run Stage 5 or Stage 6 scoring to refresh a view. If the approved methodology changes, the official scoring and sensitivity outputs must be regenerated and revalidated before the dashboard is updated.
