# SupeRR Selector — Season 2

SupeRR Selector is a pressure-adjusted T20 cricket analytics project covering IPL and T20I cricket. It produces independent batter and bowler rankings from ball-by-ball pressure performance, then stress-tests those rankings across a registered sensitivity programme.

The repository contains the Stage 1–6 analysis pipeline, its validation reports, and the **Stage 7 Streamlit dashboard** that presents the approved results. The dashboard is a read-only presentation layer: it never recalculates pressure, re-scores players, changes eligibility, or reruns a scenario.

## Dashboard

The dashboard answers four questions:

1. Who are the approved top-10 batters and bowlers?
2. How does an individual player compare with their own baseline under pressure?
3. How stable is a ranking across the approved Stage 6 scenarios?
4. Which methodology rules and limitations travel with the results?

### Pages

| Page | Contents |
| :--- | :--- |
| **Overview** | Six KPI cards, approved top-ranked players, eligibility funnel, top-10 snapshots and validation status |
| **Top 10 Batters** | Podium, name/ID search, format filter, sort controls, approved ranking table, audit view and CSV download |
| **Top 10 Bowlers** | Same layout and controls for the approved bowler ranking |
| **Player Analysis** | Name/ID search, dual-role switching, pressure-vs-baseline records, format scores, reliability, sample size and detailed records |
| **Ranking Comparison** | Scenario-group filtering, top-10 overlap, Jaccard, Spearman rho, Kendall tau, rank movement, membership detail and correlation charts |
| **Data and Methodology** | Coverage, eligibility, scoring rules, reliability calibration, limitations, validation evidence and the scenario register |

The sidebar includes navigation, validation status, and an opt-in toggle for the 10 supplementary sensitivity diagnostics. Primary scores and ranks are never affected by display controls.

### Headline results

| Metric | Value |
| :--- | ---: |
| Scoring matches | 812 |
| Scoring deliveries | 191,963 |
| Eligible batters | 101 |
| Eligible bowlers | 141 |
| Dual-role players | 23 |
| Approved scenarios | 21 (primary + 20 approved alternatives) |
| Supplementary diagnostics | 10 (opt-in only) |
| Completed sensitivity runs | 31 |
| Stage 5 validation checks | 70 / 70 |
| Stage 6 validation checks | 23 / 23 |

The approved top-10 order, composite scores, reliability values and effective sample sizes are reproduced exactly from the Stage 5 CSV outputs.

## Repository layout

```text
SupeRR-Selector-S2/
├── dashboard/              Stage 7 Streamlit application
│   ├── app.py              Entry point and navigation
│   ├── theme.py            Design tokens and responsive CSS
│   ├── components.py       Shared UI components
│   ├── charts.py           Plotly chart builders
│   ├── core.py             Approved-output loading and table logic
│   └── pages.py            Six page renderers
├── outputs/
│   ├── stage5/             Approved Stage 5 scoring and ranking CSVs
│   └── stage6/             Approved Stage 6 sensitivity CSVs
├── src/                    Stage 1–6 data, feature, scoring and sensitivity code
├── tests/                  Stage 1–6 tests plus dashboard regression tests
├── reports/                Methodology, validation and dashboard documentation
├── .streamlit/config.toml  Dark theme and minimal toolbar
├── requirements.txt        Dashboard runtime dependencies
└── requirements-dev.txt    Additional dependency for the Stage 1–6 tests
```

## Run locally

The dashboard requires Python and the four packages in `requirements.txt`. No network connection is needed at runtime.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

Streamlit opens `http://localhost:8501`. To use another port or run headless:

```bash
python -m streamlit run dashboard/app.py --server.port 8507 --server.headless true
```

The application resolves all data paths relative to the repository, so it can be launched from any working directory.

## Deploy to Streamlit Community Cloud

1. Publish this repository to GitHub. The approved Stage 5 and Stage 6 CSVs are included, so the dashboard has everything it needs.
2. In Streamlit Community Cloud, create an app and set the **main file path** to `dashboard/app.py`.
3. Select the repository and branch. `requirements.txt` is installed automatically, and `.streamlit/config.toml` applies the dark theme.
4. No secrets, API keys or external data connections are required.

Do **not** commit `data/raw/` or `data/processed/`. They are excluded by `.gitignore`; neither is read by the dashboard.

## Data included and excluded

### Included — required by the dashboard

**`outputs/stage5/`**

- `batter_scoring.csv`
- `bowler_scoring.csv`
- `batter_format_records.csv`
- `bowler_format_records.csv`
- `top10_batters.csv`
- `top10_bowlers.csv`

The folder also contains the approved Stage 5 audit outputs (`calibration_population.csv`, `eligibility_audit.csv`, `format_eligibility_audit.csv`). These are not read by the dashboard but are retained as approved evidence.

**`outputs/stage6/`**

- `player_rank_changes.csv`
- `batter_sensitivity_rankings.csv`
- `bowler_sensitivity_rankings.csv`
- `sensitivity_summary.csv`
- `batter_top10_stability.csv`
- `bowler_top10_stability.csv`
- `eligibility_sensitivity.csv`
- `scenario_diagnostics.csv`
- `stage6_validation_checks.csv`

These 15 CSVs total about 7.4 MB and are the dashboard's complete data dependency.

### Excluded

- **`data/raw/`** — original competition datasets. They are large and are not redistributed with this repository. Place them there only if you have the right to use them.
- **`data/processed/`** — large derived intermediates (several hundred MB). They are regenerable from the pipeline and are **not** read by the dashboard.
- Virtual environments, caches, logs, secrets and temporary files.

## Methodology summary

Stage 5 builds format-level hitting and bowling records, applies the approved minimum-sample and match-breadth gates, shrinks small samples with Kish effective sample sizes, standardises against the approved moments, weights the components 30/25/20/15/10, and calibrates a 0–100 reliability index. Ranks are deterministic with published tie-breaks.

Stage 6 re-runs the same engine across the registered approved alternatives and supplementary diagnostics, reporting eligible counts, top-10 membership, rank movement and rank correlations against the primary ranking.

Detailed rules, constants and validation evidence are in the reports listed below. The CSVs remain the authoritative record.

## Data limitations

- **Season sensitivity:** `SEASON_EQUAL` and `SEASON_2024_2026` fall below the approved `rho > 0.92` stability target. The primary ranking is not season-invariant.
- **Top-10 turnover:** a 6/10 or 7/10 overlap means members changed, not that every player moved by that many places. Individual rank movements can be larger.
- **`PROVISIONAL_OTHER`:** the cricket meaning of `other` extras remains unresolved. The primary bowler boundary-conceded treatment uses the provisional all-extras rule.
- **Match 48610:** the DLS provenance is unresolved. The 93 second-innings chase rows are excluded from primary pressure and baselines; the P1 fallback is a sensitivity/audit device only.
- **No combined all-rounder score:** batter and bowler rankings are independent. Dual-role players appear in both where eligible, but no combined ranking exists.
- **Display precision:** scores are rounded for readability. The approved CSVs are authoritative.
- **Runtime dependency:** if a required output is missing, the dashboard stops with a clear error rather than substituting values.
- **Narrow screens:** wide tables scroll inside their own card; this does not cause page-level horizontal overflow.

## Tests

Dashboard regression tests need only the included outputs:

```bash
python -m unittest tests.test_dashboard -v
```

The complete Stage 1–6 suite additionally requires the raw and processed datasets, which are not distributed:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -p "test_*.py" -v
```

In the validated development workspace, the complete suite passes **61/61** (47 Stage 1–6 + 14 dashboard tests), and all six dashboard pages render cleanly at desktop, tablet and mobile widths.

## Documentation

- [`reports/dashboard_guide.md`](reports/dashboard_guide.md) — dashboard pages, controls, design and limitations
- [`reports/stage4_methodology_proposal.md`](reports/stage4_methodology_proposal.md) — approved methodology
- [`reports/stage5_scoring_validation.md`](reports/stage5_scoring_validation.md) — Stage 5 validation evidence
- [`reports/stage6_sensitivity_report.md`](reports/stage6_sensitivity_report.md) — sensitivity programme and results
- [`reports/data_quality_report.md`](reports/data_quality_report.md) — data cleaning and coverage
- [`reports/feature_engineering_report.md`](reports/feature_engineering_report.md) — pressure feature construction
- [`reports/stage3_validation_audit.md`](reports/stage3_validation_audit.md) — feature validation audit

## Guardrails

Do not edit the Stage 5 or Stage 6 CSVs from the dashboard. If the approved methodology changes, regenerate the official outputs with `src/` and revalidate them before updating the dashboard. Pressure scores are situational performance indicators, not a claim about a player's overall ability.
