# Stage 4.2 Technical Specification: Dual-Perspective Pressure Engine & Player Reliability Framework

**Project:** SupeRR Selector Season 2 — Identify the Most Reliable Players Under Pressure  
**Target Franchise:** Rajasthan Royals (IPL 2027 Auction & Retention Strategy)  
**Author:** Senior Cricket Analytics Researcher & Lead Data Scientist  
**Date:** November 2026  
**Revision:** Stage 4.2 — Q1–Q11 applied; scoring corpus updated to 191,963 deliveries / 812 matches  
**Document Type:** Stage 4.2 Approved Technical Specification & Mathematical Reference  
**Status:** Approved Final Methodology (Stage 4.2); Stage 5 primary scoring implemented — see `reports/stage5_scoring_validation.md`

---

## 0. Approval, Scope, and Non-Negotiable Decisions

This document is the authoritative Stage 4.2 methodology. It incorporates the 17 approved corrections, the additional approvals recorded in the Stage 4 audits, the two latest batter-attribution approvals, and all **11 Stage 4.1 approval questions (Q1–Q11)**. It supersedes all earlier drafts of this file.

**Approved in this revision:**

1. **Batter dismissal rate — Definition A is primary.** All legitimate striker dismissals are included, including dismissals on wide deliveries; the balls-faced denominator is unchanged. Definition B, which removes wide-delivery dismissals from the numerator, is retained only as a sensitivity check.
2. **Batter boundary percentage — source flags are primary.** `is_four` and `is_six` remain the boundary numerator. `batter_runs == 4 or 6` is retained only as a sensitivity proxy.
3. **All 11 Stage 4.1 approval questions (Q1–Q11) are approved exactly as recommended.** They are applied throughout this revision and consolidated in Appendix A.3.
4. **Operational scoring corpus: 191,963 deliveries across 812 matches.** This is the 192,056-row completed non-Super-Over audit corpus after excluding the 93 Match 48610 second-innings rows under Q9. The 192,056-row file remains the audit/reconciliation corpus and is not the scored population.
5. All previously approved Stage 4 decisions and corrections remain in force.

**No code, dataset, test, ranking, or other report is modified by this document.** No player rankings have been generated.

### 0.1 Analytical scope

| Cohort | Matches | Deliveries | Treatment |
| :--- | ---: | ---: | :--- |
| **Scoring corpus** — completed matches, IPL 2022–2026 and T20I 2022+ | **812** | **191,963** | **Primary pressure and ranking corpus** |
| — IPL (`match_format = T20`) | 362 | 87,217 | Primary; format-specific standardization |
| — T20I (`match_format = T20I`) | 450 | 104,746 | Primary; format-specific standardization |
| Audit corpus — completed non-Super-Over file before Q9 exclusion | 812 | 192,056 | Reconciliation and audit only; not scored |
| — Match 48610 second innings (excluded from scoring under Q9) | within 812 | 93 | Excluded from pressure and personal baselines; \(P_1\) fallback is sensitivity only |
| Interrupted / no-result | 25 | 1,932 | Preserved separately; excluded |
| Super Overs (matches already inside the 812; deliveries excluded) | 4 | 26 | Preserved separately; excluded |
| Abandoned — no balls bowled | 16 | 0 | Preserved in `cleaned_matches.csv`; excluded |
| Selected cleaned scope | 853 | 194,014 | Full reconciliation scope |

The primary scoring corpus is `data/processed/delivery_pressure_features.csv` after the Q9 exclusion: **191,963 deliveries across 812 matches**. The 192,056-row completed non-Super-Over file is retained as the audit corpus; it includes the 93 Match 48610 second-innings rows that are excluded from all primary pressure and baseline calculations. The auxiliary corpora are `data/processed/interrupted_delivery_features.csv` and `data/processed/super_over_delivery_features.csv`. The selected scope is `data/processed/cleaned_deliveries.csv`. Match reconciliation: \(812 + 25 + 16 = 853\), with the 4 Super Over matches already inside the 812. Delivery reconciliation: \(191,963 + 93 + 1,932 + 26 = 194,014\).

### 0.2 Non-negotiable values

| Decision | Final value |
| :--- | :--- |
| Batter composite weights | **30 / 25 / 20 / 15 / 10** |
| Bowler composite weights | **30 / 25 / 20 / 15 / 10** |
| Format eligibility \(F_{j,r}\) | **\(N_{raw} \ge 75\)**, **\(N_{eff,del} \ge 35\)**, baseline sufficient, all five metric denominators \(>0\), finite \(Z_{comp}\) |
| Final ranking eligibility | **\(F_{j,r}\) non-empty AND \(M_{role,j,r} \ge 10\)** |
| Calibration population | **\(F_{j,r}\) non-empty; \(M \ge 10\) NOT applied** |
| Shrinkage constant | **\(K = 50\)** |
| Reliability slope | **\(\gamma = 0.80\)** |
| Replacement-level reliability | **50.0** at \(Z^*_{std} = 0\) (the calibration-population mean) |
| Batter calibration constants | **\(\mu_{Zcomp} = 0.1036068081\)**, **\(\sigma_{Zcomp} = 0.6610638828\)** (\(n = 122\)) |
| Bowler calibration constants | **\(\mu_{Zcomp} = 0.0256919707\)**, **\(\sigma_{Zcomp} = 0.6655792246\)** (\(n = 173\)) |
| Primary all-innings CRR | IPL **9.3201**, T20I **8.5516** |
| First-innings CRR comparison | IPL **9.3749**, T20I **8.6673** |
| Wicket baseline | IPL **6.2624**, T20I **6.7867** |
| Bowling Gaussian width | **\(\sigma_S = 12\)** runs |
| Binary leverage | **\(Leverage_{binary} = 3.00\)** |

These are the locked Stage 4.2 values. The CRR, wicket-baseline, Gaussian-width, and leverage values are unchanged. The T20I reference moments and calibration constants in Sections 10–11 are the approved post-Q9 values computed on the 191,963-delivery scoring corpus.

### 0.3 Pressure scores are not performance scores

\(P_{bat}\) and \(P_{bowl}\) are **situational pressure indices**. Higher values mean more pressure on the batter or bowler in that delivery state. They are not measures of player quality, and they are not performance scores. All performance metrics and all composite Z-scores are oriented so that **positive values mean better performance**.

---

## 1. Executive Summary & Foundational Architecture

In Twenty20 cricket, pressure is an asymmetric, role-specific operational stress state. The same match state can be extreme for the batter and mild for the bowler, or vice versa. This specification therefore builds two separate pressure engines and two separate performance composites.

The framework produces:

1. **\(P_{bat} \in [0,100]\)** — batter pressure, driven by scoring velocity, delivery expiration, wicket depletion, and chase demand.
2. **\(P_{bowl} \in [0,100]\)** — bowler pressure, driven by the relationship between expected scoring and the runs required, resource depth, time decay, and binary finish leverage.
3. **\(N_{eff}\)** — Kish effective sample size, separating opportunity volume from execution quality and supplying the shrinkage denominator.
4. **\(\text{Reliability} \in [0,100]\)** — a bounded, shrinkage- and calibration-adjusted score representing pressure performance relative to format peers and personal baselines.

All performance outputs are produced **separately for batters and bowlers**. The primary ranking has **one row per player per role**; all-rounders qualify independently in each role, and there is **no combined all-rounder ranking** in the primary analysis.

### 1.1 Architectural ground rules

- **Zero pre-delivery leakage.** Every pressure input is computed strictly from the state before the delivery: `runs_before`, `wickets_before`, `legal_balls_before`, `max_balls`, and the pre-delivery target state.
- **Dynamic innings horizon.** Every horizon function uses the match-specific `max_balls`, not a fixed 120-ball assumption. Rain-shortened matches scale exactly.
- **Strict cricket attribution.** Bowlers receive only legitimate wickets (`Caught`, `Bowled`, `LBW`, `Stump`, `Hit Wicket`). Run-outs, retire-outs, and obstructing the field are excluded from bowler credit. Wides do not count as balls faced. Byes and leg-byes are not charged to bowler economy.
- **Format-specific standardization.** Raw metrics are standardized within IPL or T20I before any cross-format combination.
- **Performance sign convention.** Positive metric values and positive Z-scores always mean better performance. Inverted metrics are given explicit negative signs in the composite equations.

### 1.2 What this document does not do

It does not alter datasets or change any approved threshold. It is the final Stage 4.2 methodology reference; the Stage 5 implementation and its validation are documented separately in `reports/stage5_scoring_validation.md`.

---

## 2. Data Scope, Baselines, and Phase Definitions

### 2.1 Baseline estimation

The primary scoring baseline is the **all-innings** completed-match run rate. The first-innings run rate is retained as a comparison and sensitivity input, but it is not the primary pressure-engine baseline.

| Parameter | IPL (T20) | T20I | Scope | Use |
| :--- | ---: | ---: | :--- | :--- |
| All-innings \(CRR_{base}\) | **9.3201** | **8.5516** | 812 completed matches | **Primary** |
| First-innings \(CRR_{base}\) | **9.3749** | **8.6673** | First innings only | Comparison / sensitivity |
| First-innings \(\lambda_w\) | **6.2624** | **6.7867** | Average wickets lost per first innings | Expected-wickets curve |
| All-innings run rate gap | **+0.7685** | — | IPL minus T20I | Format parity context |

The all-innings baseline is primary because the pressure engine operates on both innings. A first-innings-only baseline would understate the scoring environment faced in chases. The first-innings values are retained so that the effect of this choice can be tested.

### 2.2 Phase run rates — informational only

Phase RPO values are reported for context. They are **not** used in any pressure equation, weight, threshold, or composite.

| Phase | IPL all innings | IPL first innings | T20I all innings | T20I first innings |
| :--- | ---: | ---: | ---: | ---: |
| Powerplay | 9.1484 | 9.0916 | 8.3189 | 8.2049 |
| Middle | 8.8311 | 8.7551 | 8.1872 | 8.2567 |
| Death | 11.0651 | 11.4098 | 10.1114 | 10.4575 |

### 2.3 Proportional phase boundaries

Phase classification is proportional to the match-specific horizon:

\[
\text{POWERPLAY}: \quad \text{legal\_balls\_before} < 0.30 \times \text{max\_balls}
\]

\[
\text{MIDDLE}: \quad 0.30 \times \text{max\_balls} \le \text{legal\_balls\_before} < 0.80 \times \text{max\_balls}
\]

\[
\text{DEATH}: \quad \text{legal\_balls\_before} \ge 0.80 \times \text{max\_balls}
\]

For a full 120-ball innings:

- Powerplay: balls **0–35** (overs 1–6).
- Middle: balls **36–95** (overs 7–16).
- Death: balls **96–119** (overs 17–20).

The Death phase is therefore **overs 17–20**, not overs 16–20. The proportional boundaries apply identically to shortened innings.

### 2.4 Balls remaining and invalid deliveries

For every delivery:

\[
\text{balls\_rem}_i = \text{max\_balls} - \text{legal\_balls\_before}_i
\]

There is **no clamping to 1**. If \(\text{balls\_rem}_i \le 0\), the delivery is classified `INVALID` and excluded from pressure and performance calculations. A zero-ball delivery is not a valid pressure observation. The same rule applies if `max_balls` is missing or non-positive.

In the current completed corpus, **zero rows** have `balls_rem <= 0`; the rule is retained for future data and for reproducibility.

### 2.5 Target provenance

Second-innings target states are stratified as:

| Provenance | Meaning | Chase treatment |
| :--- | :--- | :--- |
| `STANDARD_TARGET` | First-innings total + 1, including equal-overs curtailed matches | Chase equations |
| `VERIFIED_REVISED_TARGET` | Genuine DLS resource-asymmetry target validated by match conclusion | Chase equations |
| `UNRESOLVED_TARGET` | Match 48610 and interrupted matches | Chase features `NaN`; Match 48610 second innings excluded from the primary scoring corpus under Q9; \(P_1\) fallback is sensitivity only |
| `NOT_APPLICABLE` | First innings | First-innings equations |

---

## 3. Decoupled Pressure Architecture

### 3.1 Operational asymmetry

| Match state | Batter incentive | Bowler incentive | Expected direction |
| :--- | :--- | :--- | :--- |
| Very high required rate, many wickets in hand | Must accelerate improbably; wickets offer some licence to attack | Defending a large cushion; a dot or single is enough | \(P_{bat}\) high; \(P_{bowl}\) low |
| Very high required rate, few wickets in hand | Collapse risk is immediate; batting resources are thin | Tail is exposed; bowler has resource dominance | \(P_{bat}\) extreme; \(P_{bowl}\) low |
| Low required rate, many wickets in hand | Comfortable cruise; low volatility | Match virtually decided; little threat | \(P_{bat}\) low; \(P_{bowl}\) low |
| Tight required rate, few wickets in hand, final balls | Every ball can decide the match | Every ball can decide the match | Both extreme; binary leverage may fire |
| Tight required rate, wickets in hand, final balls | Must execute under execution stress | Must defend a narrow margin | Both high |

The directions above are qualitative. Exact values are given by the equations and the canonical scenarios in Section 5.

### 3.2 Why the two engines are separate

A single symmetric pressure scalar would force the same state to have the same pressure for both roles. That is empirically false. The batter's pressure is driven by required scoring velocity and dismissal risk; the bowler's pressure is driven by the gap between expected scoring and the runs required, plus resource depth and time. The two engines therefore use different state variables and different link functions.

---

## 4. Mathematical Formulation: First-Innings Pressure (\(P_1\))

In the first innings there is no fixed target. Pressure is driven by resource depletion relative to format scoring expectations and by delivery expiration.

### 4.1 Dynamic horizon functions

Let \(\text{max\_balls} = \text{overs\_limit} \times 6\). For any delivery \(i\), let \(b_i = \text{legal\_balls\_before}_i\).

#### A. Expected cumulative runs

\[
\text{ExpectedRuns}(b_i,\text{format},\text{max\_balls}) = CRR_{base}(\text{format}) \times \frac{b_i}{6.0}
\]

#### B. Expected cumulative wickets

\[
\text{ExpectedWickets}(b_i,\text{format},\text{max\_balls}) = \lambda_w(\text{format}) \times \left(\frac{\text{max\_balls}}{120.0}\right) \times \left(\frac{b_i}{\text{max\_balls}}\right)^{0.85}
\]

For a 10-over match, the total expected wickets scale to \(6.2624 \times (60/120) = 3.1312\) in IPL and \(6.7867 \times (60/120) = 3.3934\) in T20I at \(b = 60\).

#### C. Phase urgency

\[
U_{phase}(b_i,\text{max\_balls}) = \left(\frac{b_i}{\text{max\_balls}}\right)^{1.50}
\]

For a 10-over match at over 9.0 (\(b=54\)), \(U_{phase} = (54/60)^{1.5} \approx 0.854\), matching over 18.0 in a 20-over match: \((108/120)^{1.5} \approx 0.854\).

#### D. Early-innings stabilization

\[
W_{stab}(b_i) = \frac{b_i}{b_i + 12.0}
\]

### 4.2 Core first-innings state variables

#### 1. Cumulative scoring-par deviation

\[
\Delta Runs(b_i) = \text{ExpectedRuns}(b_i,\text{format},\text{max\_balls}) - \text{runs\_before}_i
\]

\[
S_{runs} = \tanh\left(\frac{\Delta Runs(b_i)}{15.0}\right)
\]

Positive \(S_{runs}\) means the batting side is **behind** par; negative means it is **ahead** of par.

#### 2. Wicket depletion strain

\[
S_{wickets} = \text{clip}\left(\frac{\text{wickets\_before}_i}{\text{ExpectedWickets}(b_i,\text{format},\text{max\_balls}) + 0.50}, 0.0, 3.0\right) \div 3.0
\]

The \(\epsilon = 0.50\) prior prevents division-by-zero and extreme opening-over spikes.

### 4.3 First-innings master equations

#### Batter pressure

\[
Z_{bat,1} = 2.20 \cdot S_{wickets} + 1.80 \cdot (W_{stab} \cdot S_{runs}) + 1.50 \cdot U_{phase} - 1.50
\]

\[
P_{bat,1} = 100 \times \frac{1}{1 + \exp\left(-Z_{bat,1}\right)}
\]

#### Bowler pressure

\[
Z_{bowl,1} = 2.00 \cdot (-S_{runs}) + 1.50 \cdot (1.0 - S_{wickets}) + 1.80 \cdot U_{phase} - 1.80
\]

\[
P_{bowl,1} = 100 \times \frac{1}{1 + \exp\left(-Z_{bowl,1}\right)}
\]

The first-innings bowler equation is unchanged. It rewards a bowler when the batting side is behind par (\(S_{runs}>0\)) and when wickets have fallen, while increasing pressure as the innings reaches its end.

---

## 5. Mathematical Formulation: Second-Innings Chase Pressure (\(P_2\))

In the second innings, pressure is governed by the feasibility of reaching the target before balls or wickets expire.

### 5.1 Variables and domains

| Variable | Definition | Domain | Role |
| :--- | :--- | :---: | :--- |
| \(\text{balls\_rem}_i\) | \(\text{max\_balls} - \text{legal\_balls\_before}_i\) | \((0,\text{max\_balls}]\) for active rows | Pre-delivery balls remaining |
| \(\text{runs\_req}_i\) | \(\text{target\_score} - \text{runs\_before}_i\) | \([0,\infty)\) | Pre-delivery runs needed |
| \(RRR_i\) | \(6.0 \times \text{runs\_req}_i / \text{balls\_rem}_i\) | \([0,\infty)\) | Required run rate |
| \(\theta_{RRR}\) | \(RRR_i / CRR_{base}(\text{format})\) | \([0,\infty)\) | Normalized rate strain |
| \(TimeDecay\) | \((\text{legal\_balls\_before}_i / \text{max\_balls})^{0.75}\) | \([0,1)\) | Temporal proximity to completion |
| \(W_{rem}\) | \(10 - \text{wickets\_before}_i\) | \([1,10]\) | Wickets in hand |
| \(Surplus\) | \(\text{ExpectedRuns}_{bowl} - \text{runs\_req}_i\) | \((-\infty,\infty)\) | Bowler's expected-run surplus |

Rows with `balls_rem <= 0`, missing targets, or `is_target_reached_before = True` are excluded before these calculations.

### 5.2 Batter chase pressure

\[
Demand_{bat} = \theta_{RRR} \times \left(\frac{10.0}{W_{rem} + 1.0}\right)^{0.60}
\]

\[
Z_{bat,2} = 2.50 \cdot \ln\left(\max(0.10, Demand_{bat})\right) + 1.80 \cdot TimeDecay - 1.20
\]

\[
P_{bat,2} = 100 \times \frac{1}{1 + \exp\left(-Z_{bat,2}\right)}
\]

The floor of 0.10 inside the logarithm prevents undefined values when the required rate is very low. It does not impose an artificial ceiling on pressure.

### 5.3 Bowler chase pressure — approved surplus-based Gaussian equation

The previous `Tension + Threat` bowling equation is **retired**. The approved formulation is:

\[
h = L_i = \sqrt{\frac{W_{rem}}{10.0}}
\]

\[
\text{ExpectedRuns}_{bowl} = CRR_{base}(\text{format}) \times \frac{\text{balls\_rem}_i}{6.0} \times h
\]

\[
Surplus = \text{ExpectedRuns}_{bowl} - \text{runs\_req}_i
\]

\[
C_{match} = \exp\left(-\frac{Surplus^2}{2\sigma_S^2}\right), \qquad \sigma_S = 12
\]

\[
core = 5.50 \cdot \left(0.65 + 0.35 \cdot h\right) + 1.20 \cdot TimeDecay
\]

\[
Z_{bowl,2} = C_{match} \cdot core + Leverage_{binary} - 4.20
\]

\[
P_{bowl,2} = 100 \times \frac{1}{1 + \exp\left(-Z_{bowl,2}\right)}
\]

The explicit constant is **\(-4.20\)**. The Gaussian width is **\(\sigma_S = 12\) runs**. The resource-depth term is **\(h = L_i = \sqrt{W_{rem}/10}\)**.

#### Interpretation

- \(C_{match}\) is a tightness kernel. It equals 1 when expected runs exactly equal runs required (\(Surplus = 0\)) and decays as the absolute surplus grows. A match that is already decided in either direction is low-pressure for the bowler.
- \(core\) rises with wickets in hand and with time decay. A tight match late, with batting resources intact, is the highest-pressure state.
- \(Leverage_{binary}\) is a step increase for the final-over, one-wicket, single-stroke state.
- The \(-4.20\) intercept centres the non-leverage state.

#### Binary climax trigger

\[
Leverage_{binary} =
\begin{cases}
3.00 & \text{if } \text{balls\_rem}_i \le 12 \ \land \ 0 < \text{runs\_req}_i \le 12 \ \land \ W_{rem} = 1 \\
0.00 & \text{otherwise}
\end{cases}
\]

The condition \(\text{runs\_req}_i > 0\) is explicit. A target already reached is not a valid chase state.

#### Monotonicity

\(P_{bowl,2}\) is **not globally monotonic in \(Surplus\)**. It peaks at \(Surplus = 0\) and declines as \(|Surplus|\) grows. This is intentional: a bowler is under maximum pressure when the match is tight, not when the batting side is either far ahead or far behind. Validation tests must therefore assert monotonicity in \(|Surplus|\) away from zero, not a global negative slope.

---

## 6. Canonical Scenarios

The eight scenarios below are the approved demonstration set. All use the IPL all-innings baseline \(CRR_{base}=9.3201\), \(\lambda_w=6.2624\), and \(\sigma_S=12\). Scenario S8 uses a 60-ball innings.

### 6.1 Scenario definitions and pressure outputs

| ID | State | \(b\) | \(\text{max\_balls}\) | \(\text{balls\_rem}\) | \(\text{runs\_req}\) | \(RRR\) | \(W_{rem}\) | \(P_{bat}\) | \(P_{bowl}\) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **S1** | High RRR, 8 wickets | 96 | 120 | 24 | 48 | 12.00 | 8 | **75.3** | **23.0** |
| **S2** | High RRR, 2 wickets | 96 | 120 | 24 | 48 | 12.00 | 2 | **94.0** | **1.8** |
| **S3** | Binary climax, 1 wicket | 114 | 120 | 6 | 6 | 6.00 | 1 | **86.4** | **98.1** |
| **S4** | Low RRR, 10 wickets | 90 | 120 | 30 | 24 | 4.80 | 10 | **17.5** | **4.3** |
| **S5** | Massive margin, 6 wickets | 114 | 120 | 6 | 42 | 42.00 | 6 | **99.2** | **1.6** |
| **S6** | Narrow margin, 2 wickets | 117 | 120 | 3 | 4 | 8.00 | 2 | **88.0** | **79.3** |
| **S7** | Moderate chase, 5 wickets | 102 | 120 | 18 | 30 | 10.00 | 5 | **79.2** | **49.3** |
| **S8** | Rain-shortened, 8 wickets | 30 | 60 | 30 | 45 | 9.00 | 8 | **48.5** | **83.0** |

### 6.2 Batter-side intermediates

| ID | \(\theta_{RRR}\) | \(Demand_{bat}\) | \(TimeDecay\) | \(Z_{bat,2}\) | \(P_{bat}\) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| S1 | 1.2875 | 1.3716 | 0.8459 | +1.1125 | 75.3 |
| S2 | 1.2875 | 2.6515 | 0.8459 | +2.7604 | 94.0 |
| S3 | 0.6438 | 1.6909 | 0.9623 | +1.8452 | 86.4 |
| S4 | 0.5150 | 0.4864 | 0.8059 | -1.5512 | 17.5 |
| S5 | 4.5064 | 5.5817 | 0.9623 | +4.8308 | 99.2 |
| S6 | 0.8584 | 1.7677 | 0.9812 | +1.9903 | 88.0 |
| S7 | 1.0729 | 1.4578 | 0.8852 | +1.3357 | 79.2 |
| S8 | 0.9657 | 1.0287 | 0.5946 | -0.0590 | 48.5 |

### 6.3 Bowler-side intermediates

| ID | \(h\) | \(\text{ExpectedRuns}_{bowl}\) | \(Surplus\) | \(C_{match}\) | \(core\) | \(Leverage_{binary}\) | \(Z_{bowl,2}\) | \(P_{bowl}\) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| S1 | 0.8944 | 33.3446 | -14.6554 | 0.4744 | 6.3118 | 0 | -1.2058 | 23.0 |
| S2 | 0.4472 | 16.6723 | -31.3277 | 0.0331 | 5.4510 | 0 | -4.0195 | 1.8 |
| S3 | 0.3162 | 2.9473 | -3.0527 | 0.9682 | 5.3385 | 3 | +3.9685 | 98.1 |
| S4 | 1.0000 | 46.6005 | +22.6005 | 0.1697 | 6.4671 | 0 | -3.1023 | 4.3 |
| S5 | 0.7746 | 7.2193 | -34.7807 | 0.0150 | 6.2208 | 0 | -4.1067 | 1.6 |
| S6 | 0.4472 | 2.0840 | -1.9160 | 0.9873 | 5.6133 | 0 | +1.3422 | 79.3 |
| S7 | 0.7071 | 19.7709 | -10.2291 | 0.6954 | 5.9985 | 0 | -0.0288 | 49.3 |
| S8 | 0.8944 | 41.6808 | -3.3192 | 0.9625 | 6.0103 | 0 | +1.5847 | 83.0 |

### 6.4 Scenario interpretation

- **S1 vs S2** isolates resource depth. The same 48-off-24 state is high batter pressure in both, but the bowler is almost without pressure when only two wickets remain because the expected-run surplus is deeply negative (-31.33).
- **S3** is the binary climax: 6 off 6 with one wicket. The trigger fires and adds 3.00, producing \(P_{bowl}=98.1\).
- **S4** is a comfortable chase: 24 off 30 with ten wickets. Expected runs (46.60) far exceed the requirement, so both pressures are low.
- **S5** is the massive-margin case: 42 off 6 with six wickets. The batter is at 99.2, but the bowler is at 1.6 because the required task is nearly impossible.
- **S6** is a narrow final-over margin: 4 off 3 with two wickets. Both sides are under high pressure (88.0 and 79.3).
- **S7** is a moderate chase: 30 off 18 with five wickets. Batter pressure is high (79.2); bowler pressure is moderate (49.3).
- **S8** shows the dynamic horizon: 45 off 30 in a 10-over match. The shorter horizon raises time-decay pressure, and the small negative surplus keeps the bowler at 83.0.

---

## 7. Worked Mathematical Examples

All examples use the approved primary baselines: IPL \(CRR_{base}=9.3201\), \(\lambda_w=6.2624\), and \(\sigma_S=12\). The six examples cover two first-innings states and four chase states, including a rain-shortened chase and the binary trigger.

### 7.1 Worked Example 1 — Rain-shortened first innings (12 overs, over 9.2)

**Parameters:** \(\text{max\_balls}=72\); \(b=56\); score \(82/3\).

**Expected curves:**

\[
\text{ExpectedRuns} = 9.3201 \times \frac{56}{6.0} = 86.9876
\]

\[
\text{ExpectedWickets} = 6.2624 \times \frac{72}{120} \times \left(\frac{56}{72}\right)^{0.85} = 3.0347
\]

**State variables:**

\[
\Delta Runs = 86.9876 - 82 = +4.9876
\]

\[
S_{runs} = \tanh(4.9876/15.0) = +0.3208
\]

\[
S_{wickets} = \text{clip}\left(\frac{3}{3.0347+0.50},0,3\right)\div 3 = 0.2829
\]

\[
W_{stab} = \frac{56}{56+12} = 0.8235, \qquad U_{phase} = \left(\frac{56}{72}\right)^{1.5} = 0.6859
\]

**Pressures:**

\[
Z_{bat,1} = 2.20(0.2829) + 1.80(0.8235 \times 0.3208) + 1.50(0.6859) - 1.50 = +0.6268
\]

\[
P_{bat,1} = \frac{100}{1+\exp(-0.6268)} = \mathbf{65.2}
\]

\[
Z_{bowl,1} = 2.00(-0.3208) + 1.50(1-0.2829) + 1.80(0.6859) - 1.80 = -0.1312
\]

\[
P_{bowl,1} = \frac{100}{1+\exp(0.1312)} = \mathbf{46.7}
\]

The batting side is slightly behind par in a shortened innings; both pressures are moderate.

### 7.2 Worked Example 2 — Early collapse (first innings, over 4.3, 20 overs)

**Parameters:** \(\text{max\_balls}=120\); \(b=27\); score \(22/4\).

**Expected curves:**

\[
\text{ExpectedRuns} = 9.3201 \times \frac{27}{6.0} = 41.9404
\]

\[
\text{ExpectedWickets} = 6.2624 \times \left(\frac{27}{120}\right)^{0.85} = 1.7624
\]

**State variables:**

\[
\Delta Runs = 41.9404 - 22 = +19.9404
\]

\[
S_{runs} = \tanh(19.9404/15.0) = +0.8691
\]

\[
S_{wickets} = \text{clip}\left(\frac{4}{1.7624+0.50},0,3\right)\div 3 = 0.5894
\]

\[
W_{stab} = \frac{27}{39} = 0.6923, \qquad U_{phase} = \left(\frac{27}{120}\right)^{1.5} = 0.1067
\]

**Pressures:**

\[
Z_{bat,1} = 2.20(0.5894) + 1.80(0.6923 \times 0.8691) + 1.50(0.1067) - 1.50 = +1.0397
\]

\[
P_{bat,1} = \frac{100}{1+\exp(-1.0397)} = \mathbf{73.9}
\]

\[
Z_{bowl,1} = 2.00(-0.8691) + 1.50(1-0.5894) + 1.80(0.1067) - 1.80 = -2.7301
\]

\[
P_{bowl,1} = \frac{100}{1+\exp(2.7301)} = \mathbf{6.1}
\]

The early collapse creates high batter pressure and very low bowler pressure: the bowling side is in total control.

### 7.3 Worked Example 3 — Comfortable chase (second innings, over 14.0)

**Parameters:** \(\text{max\_balls}=120\); \(b=84\); \(\text{balls\_rem}=36\); \(\text{runs\_req}=32\); \(W_{rem}=8\).

\[
RRR = \frac{32}{36}\times 6.0 = 5.3333, \qquad \theta_{RRR} = \frac{5.3333}{9.3201} = 0.5722
\]

\[
TimeDecay = \left(\frac{84}{120}\right)^{0.75} = 0.7653
\]

\[
Demand_{bat} = 0.5722 \times \left(\frac{10}{9}\right)^{0.60} = 0.6096
\]

\[
Z_{bat,2} = 2.50\ln(0.6096) + 1.80(0.7653) - 1.20 = -1.0599
\]

\[
P_{bat,2} = \frac{100}{1+\exp(1.0599)} = \mathbf{25.7}
\]

For the bowler:

\[
h = \sqrt{\frac{8}{10}} = 0.8944
\]

\[
\text{ExpectedRuns}_{bowl} = 9.3201 \times \frac{36}{6.0} \times 0.8944 = 50.0169
\]

\[
Surplus = 50.0169 - 32 = +18.0169
\]

\[
C_{match} = \exp\left(-\frac{18.0169^2}{2(12^2)}\right) = 0.3240
\]

\[
core = 5.50(0.65+0.35 \times 0.8944) + 1.20(0.7653) = 6.2151
\]

\[
Z_{bowl,2} = 0.3240(6.2151) + 0 - 4.20 = -2.1865
\]

\[
P_{bowl,2} = \frac{100}{1+\exp(2.1865)} = \mathbf{10.1}
\]

The chasing side is comfortably ahead of the expected-run curve, so both pressures are low.

### 7.4 Worked Example 4 — Extreme chase (second innings, over 19.0)

**Parameters:** \(\text{max\_balls}=120\); \(b=114\); \(\text{balls\_rem}=6\); \(\text{runs\_req}=22\); \(W_{rem}=4\).

\[
RRR = \frac{22}{6}\times 6.0 = 22.0000, \qquad \theta_{RRR} = \frac{22.0000}{9.3201} = 2.3605
\]

\[
TimeDecay = \left(\frac{114}{120}\right)^{0.75} = 0.9623
\]

\[
Demand_{bat} = 2.3605 \times \left(\frac{10}{5}\right)^{0.60} = 3.5778
\]

\[
Z_{bat,2} = 2.50\ln(3.5778) + 1.80(0.9623) - 1.20 = +3.7190
\]

\[
P_{bat,2} = \frac{100}{1+\exp(-3.7190)} = \mathbf{97.6}
\]

For the bowler:

\[
h = \sqrt{\frac{4}{10}} = 0.6325
\]

\[
\text{ExpectedRuns}_{bowl} = 9.3201 \times \frac{6}{6.0} \times 0.6325 = 5.8945
\]

\[
Surplus = 5.8945 - 22 = -16.1055
\]

\[
C_{match} = \exp\left(-\frac{(-16.1055)^2}{2(12^2)}\right) = 0.4063
\]

\[
core = 5.50(0.65+0.35 \times 0.6325) + 1.20(0.9623) = 5.9472
\]

\[
Z_{bowl,2} = 0.4063(5.9472) + 0 - 4.20 = -1.7836
\]

\[
P_{bowl,2} = \frac{100}{1+\exp(1.7836)} = \mathbf{14.4}
\]

The batting side needs 22 off 6; the bowler is defending a large expected-run cushion. Batter pressure is extreme, bowler pressure is low.

### 7.5 Worked Example 5 — Rain-shortened chase (second innings, 10 overs, over 5.0)

**Parameters:** \(\text{max\_balls}=60\); \(b=30\); \(\text{balls\_rem}=30\); \(\text{runs\_req}=45\); \(W_{rem}=7\).

\[
RRR = \frac{45}{30}\times 6.0 = 9.0000, \qquad \theta_{RRR} = \frac{9.0000}{9.3201} = 0.9657
\]

\[
TimeDecay = \left(\frac{30}{60}\right)^{0.75} = 0.5946
\]

\[
Demand_{bat} = 0.9657 \times \left(\frac{10}{8}\right)^{0.60} = 1.1040
\]

\[
Z_{bat,2} = 2.50\ln(1.1040) + 1.80(0.5946) - 1.20 = +0.1176
\]

\[
P_{bat,2} = \frac{100}{1+\exp(-0.1176)} = \mathbf{52.9}
\]

For the bowler:

\[
h = \sqrt{\frac{7}{10}} = 0.8367
\]

\[
\text{ExpectedRuns}_{bowl} = 9.3201 \times \frac{30}{6.0} \times 0.8367 = 38.9888
\]

\[
Surplus = 38.9888 - 45 = -6.0112
\]

\[
C_{match} = \exp\left(-\frac{(-6.0112)^2}{2(12^2)}\right) = 0.8821
\]

\[
core = 5.50(0.65+0.35 \times 0.8367) + 1.20(0.5946) = 5.8991
\]

\[
Z_{bowl,2} = 0.8821(5.8991) + 0 - 4.20 = +1.0035
\]

\[
P_{bowl,2} = \frac{100}{1+\exp(-1.0035)} = \mathbf{73.2}
\]

The shortened chase keeps the match tight; the bowler faces high pressure despite the moderate required rate.

### 7.6 Worked Example 6 — Final-over binary trigger (second innings, over 19.0)

**Parameters:** \(\text{max\_balls}=120\); \(b=114\); \(\text{balls\_rem}=6\); \(\text{runs\_req}=12\); \(W_{rem}=1\).

\[
RRR = \frac{12}{6}\times 6.0 = 12.0000, \qquad \theta_{RRR} = \frac{12.0000}{9.3201} = 1.2875
\]

\[
TimeDecay = 0.9623
\]

\[
Demand_{bat} = 1.2875 \times \left(\frac{10}{2}\right)^{0.60} = 3.3818
\]

\[
Z_{bat,2} = 2.50\ln(3.3818) + 1.80(0.9623) - 1.20 = +3.5781
\]

\[
P_{bat,2} = \frac{100}{1+\exp(-3.5781)} = \mathbf{97.3}
\]

For the bowler:

\[
h = \sqrt{\frac{1}{10}} = 0.3162
\]

\[
\text{ExpectedRuns}_{bowl} = 9.3201 \times \frac{6}{6.0} \times 0.3162 = 2.9473
\]

\[
Surplus = 2.9473 - 12 = -9.0527
\]

\[
C_{match} = \exp\left(-\frac{(-9.0527)^2}{2(12^2)}\right) = 0.7523
\]

\[
core = 5.50(0.65+0.35 \times 0.3162) + 1.20(0.9623) = 5.3385
\]

The trigger fires because \(\text{balls\_rem}=6 \le 12\), \(0 < \text{runs\_req}=12 \le 12\), and \(W_{rem}=1\):

\[
Leverage_{binary} = 3.00
\]

\[
Z_{bowl,2} = 0.7523(5.3385) + 3.00 - 4.20 = +2.8164
\]

\[
P_{bowl,2} = \frac{100}{1+\exp(-2.8164)} = \mathbf{94.4}
\]

This is the binary climax: one wicket wins, one boundary loses.

### 7.7 Worked-example summary

| ID | Type | \(b\) | \(\text{max\_balls}\) | \(\text{runs\_req}\) | \(W_{rem}\) | \(P_{bat}\) | \(P_{bowl}\) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| WE1 | First innings, 12 overs | 56 | 72 | — | — | 65.2 | 46.7 |
| WE2 | First innings, 20 overs | 27 | 120 | — | — | 73.9 | 6.1 |
| WE3 | Comfortable chase | 84 | 120 | 32 | 8 | 25.7 | 10.1 |
| WE4 | Extreme chase | 114 | 120 | 22 | 4 | 97.6 | 14.4 |
| WE5 | Rain-shortened chase | 30 | 60 | 45 | 7 | 52.9 | 73.2 |
| WE6 | Final-over binary trigger | 114 | 120 | 12 | 1 | 97.3 | 94.4 |

---

## 8. Performance Accounting and Attribution

Performance under pressure is calculated strictly across legitimate cricket attributions. The matrix below is the authoritative event-level reference.

**Corpus convention for this section.** Unless a table or paragraph is explicitly labelled **scoring corpus (191,963)** or **post-Q9**, descriptive event counts in Section 8 are **audit-corpus counts** from the 192,056-row completed non-Super-Over file. The operational scoring corpus is 191,963 after excluding the 93 Match 48610 second-innings rows under Q9. The difference affects counts only; no attribution, metric definition, or approved decision changes.

### 8.1 Cricket performance attribution matrix

```text
=====================================================================================================================
CRICKET PERFORMANCE ATTRIBUTION MATRIX
=====================================================================================================================
Delivery Event            Batter Runs      Batter Ball Faced?   Bowler Runs Charged      Bowler Legal Ball?   Bowler Wicket?
---------------------------------------------------------------------------------------------------------------------
Off the bat (0 to 6)      Credited (0-6)   YES                  Charged (0-6)            YES                  NO
Wide (1 to 5 extras)      0                NO                   Charged extras           NO                   Stump only
No-ball (overstep)        Credited         YES                  Batter runs + 1          NO                   No (RunOut observed)
No-ball ('other')         Credited         YES                  Batter runs + 1          NO                   No (RunOut observed)
Byes (1 to 4 extras)      0                YES                  0 (Team extra)           YES                  No (RunOut observed)
Leg-Byes (1 to 4 extras)  0                YES                  0 (Team extra)           YES                  NO
Penalty Runs              0                NO                   0 (Team extra)           Follow source flag   NO
Caught / Bowled           0                YES                  0                        YES                  YES
LBW / Stumped             0                YES                  0                        YES                  YES
Hit Wicket                0                YES                  0                        YES                  YES
Run-Out                   0                YES                  0                        YES                  NO (Fielding out)
Retire Out                0                YES                  0                        YES                  NO (Tactical out)
Obstructing Field         0                YES                  0                        YES                  NO (Behavioral)
=====================================================================================================================
```

Two details are deliberate:

- **Wide stumpings are legitimate bowler wickets.** There are **25** wide stumpings in the completed data: **15 IPL**, **10 T20I**. They are retained in the wicket-rate numerator. Wides still do not count as balls faced, and the wicket-rate denominator remains legal deliveries only. The resulting numerator/denominator asymmetry is documented in Section 8.8.
- **Wide stumpings are covered by the Wide row.** The delivery is non-legal and the batter does not face a ball, but the bowler receives a `Stump` wicket. The combined `LBW / Stumped` row refers to legal deliveries only.
- **No-ball dismissals in the current data are run-outs only.** No bowler-credited dismissal type occurs on an overstep or `other` delivery. The general rule remains dismissal-type based.

### 8.2 Bowler-credited wickets

\[
is\_bowler\_wicket_i = is\_wicket_i \land dismissal\_type_i \in \{\text{Caught, Bowled, LBW, Stump, Hit Wicket}\}
\]

Run-outs, retire-outs, and obstructing the field are **never** credited to the bowler. A wide stumping is a `Stump` dismissal and is therefore credited, even though the delivery is not legal.

### 8.3 Bowler runs conceded

There is no native `bowler_runs` column in the processed data. It must be derived exactly as:

\[
\text{bowler\_runs}_i =
\begin{cases}
\text{batter\_runs}_i + \text{extras\_runs}_i & \text{if } extras\_type_i \in \{\text{wide, overstep, other}\} \\
\text{batter\_runs}_i & \text{otherwise}
\end{cases}
\]

Consequences:

- **Wide:** batter runs are 0; the bowler is charged the wide extras.
- **Overstep:** the bowler is charged the batter runs plus the one-run no-ball penalty.
- **`other`:** provisional no-ball-like treatment; the bowler is charged batter runs plus extras. This is provisional because the `other` classification is unresolved.
- **Byes, leg-byes, penalty:** not charged to the bowler. The `otherwise` branch yields `batter_runs`, which is 0 for these events.
- **Off the bat:** the bowler is charged the batter runs.

### 8.4 Batter balls faced

\[
BF_i = \mathbb{I}(extras\_type_i \ne \text{wide})
\]

Wides do **not** count as balls faced. Oversteps and provisional `other` deliveries **do** count as balls faced, because the batter faced a delivery and can score from it. Byes and leg-byes are legal deliveries and count as balls faced. The batter-run numerator is the runs scored off the bat, not team extras.

### 8.5 Batter boundary percentage — source flags are primary

The boundary numerator is:

\[
Boundary\%_{P,j} = 100 \times
\frac{\sum_{i \in \mathcal{D}_{j,bat}} w_i \cdot \mathbb{I}(is\_four_i \lor is\_six_i)}
{\sum_{i \in \mathcal{D}_{j,bat}} w_i \cdot BF_i}
\]

`is_four` and `is_six` are source-provided **batter-boundary flags**. They are not team-boundary flags and are not derived by project code.

#### Flag consistency

| Check | Full completed | Pressure set \(P_{bat}\ge60\) |
| :--- | ---: | ---: |
| `is_four` true but `batter_runs != 4` | **0** | **0** |
| `is_six` true but `batter_runs != 6` | **0** | **0** |
| `batter_runs == 4` but `is_four` false | 20 | 7 |
| `batter_runs == 6` but `is_six` false | 3 | 0 |

The 20 fours and 3 sixes without flags are consistent with all-run fours and sixes, not boundary shots. The source has no independent boundary-distance field, so this is a strong inference rather than a directly verified boundary flag.

#### Counts by extras type — full completed audit corpus (192,056)

| Extras type | Rows | `is_four` | `is_six` | `batter_runs=4` | `batter_runs=6` |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Byes | 505 | 0 | 0 | 0 | 0 |
| Leg-byes | 2,633 | 0 | 0 | 0 | 0 |
| Legal off bat (`none`) | 180,692 | 22,329 | 12,214 | 22,349 | 12,217 |
| `other` | 256 | 40 | 26 | 40 | 26 |
| Overstep | 556 | 79 | 45 | 79 | 45 |
| Penalty | 1 | 0 | 0 | 0 | 0 |
| Wide | 7,413 | 0 | 0 | 0 | 0 |
| **Total** | **192,056** | **22,448** | **12,285** | **22,468** | **12,288** |

#### Counts by extras type — pressure set \(P_{bat}\ge60\) (audit corpus)

| Extras type | Rows | `is_four` | `is_six` | `batter_runs=4` | `batter_runs=6` |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Byes | 219 | 0 | 0 | 0 | 0 |
| Leg-byes | 883 | 0 | 0 | 0 | 0 |
| Legal off bat (`none`) | 63,638 | 6,480 | 4,459 | 6,487 | 4,459 |
| `other` | 117 | 15 | 12 | 15 | 12 |
| Overstep | 191 | 27 | 19 | 27 | 19 |
| Penalty | 1 | 0 | 0 | 0 | 0 |
| Wide | 2,831 | 0 | 0 | 0 | 0 |
| **Total** | **67,880** | **6,522** | **4,490** | **6,529** | **4,490** |

#### Flag numerator versus runs proxy

| Scope | Flag-based boundaries | `batter_runs in {4,6}` proxy | Difference |
| :--- | ---: | ---: | ---: |
| Full completed | 34,733 | 34,756 | **+23** |
| Pressure set | 11,012 | 11,019 | **+7** |

The pressure-set difference is exactly **7 all-run fours**. There are no all-run sixes in the pressure set. The runs proxy overcounts boundary events and is therefore **not** the primary metric.

#### Player-level impact of the runs proxy

Only six batter-format records are affected. `n_flag` and `n_runs` are unweighted counts; the percentages are weighted.

| Format | Batter | \(N_{raw}\) | BF | \(M\) | \(n_{flag}\) | \(n_{runs}\) | \(BP_{flag}\%\) | \(BP_{runs}\%\) | \(\Delta BP\) pp | \(\lambda_{BF}\) | Eligible | \(0.20\Delta z\) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: | ---: |
| T20 | Donovan Ferreira | 116 | 114 | 8 | 23 | 24 | 19.716 | 20.802 | +1.086 | 0.688277 | No | +0.0481 |
| T20 | Vipraj Nigam | 63 | 60 | 7 | 19 | 20 | 32.686 | 34.297 | +1.611 | 0.541194 | No | +0.0562 |
| T20I | Ryan Burl | 515 | 493 | 31 | 68 | 69 | 14.897 | 15.142 | +0.245 | 0.902286 | Yes | +0.0127 |
| T20I | Najibullah Zadran | 197 | 183 | 16 | 31 | 33 | 18.254 | 19.141 | +0.887 | 0.778923 | Yes | **+0.0407** |
| T20I | Jason Holder | 270 | 259 | 30 | 46 | 47 | 19.651 | 20.172 | +0.521 | 0.829485 | Yes | +0.0251 |
| T20I | Matheesha Pathirana | 32 | 32 | 9 | 1 | 2 | 2.191 | 5.966 | +3.774 | 0.382499 | No | +0.0866 |

Three affected records are eligible; the proxy would raise their composite by **+0.0127 to +0.0407**. The largest eligible shift is Najibullah Zadran at **+0.0407**. Pathirana's +0.0866 is larger but he is ineligible.

**Decision:** keep `is_four | is_six` as the primary boundary numerator. Keep `batter_runs == 4 or 6` only as the `BOUNDARY_RUNS_PROXY` sensitivity. No weight change.

#### Reference values for the flag metric

| Format | \(\mu_{peer}\) | Players | Reference n | Mean | SD |
| :--- | ---: | ---: | ---: | ---: | ---: |
| T20 | 15.242915 | 303 | 101 | 18.412502 | 3.079949 |
| T20I | 12.937251 | 603 | 142 | 16.005504 | 3.335999 |

The runs-proxy sensitivity has its own format-specific reference values: T20 mean 18.421896, SD 3.080243; T20I mean 16.017383, SD 3.339804.

T20 values are unchanged. T20I values are the approved post-Q9 scoring-corpus values (191,963 deliveries); the pre-Q9 audit values are superseded.

### 8.6 Dot balls

The approved dot-ball definition is:

\[
is\_dot_i = \mathbb{I}(team\_runs_i = 0 \land is\_legal\_delivery_i)
\]

Consequences:

- A legal zero-run wicket delivery is a dot. Wicket status does not change the dot definition.
- A non-legal delivery is never a dot, even if zero runs are recorded.

#### Verified counts — completed non-Super-Over audit corpus (192,056)

| Quantity | Count |
| :--- | ---: |
| Legal dots (`team_runs=0`, legal) | **64,785** |
| Non-legal zero-run deliveries | **0** |
| Legal zero-run wicket deliveries | **10,105** |
| — of which bowler-credited wickets | **9,779** |
| — of which run-out / retire / obstructing | **326** |

All 10,105 legal zero-run wicket deliveries are dots under the definition. The **9,779** figure is the approved audit anchor for legal zero-run **bowler-wicket** balls; it is a subset of the 10,105, not a different dot definition.

#### Dot percentages

For batters:

\[
Dot\%_{P,j} = 100 \times
\frac{\sum_{i \in \mathcal{D}_{j,bat}} w_i \cdot is\_dot_i}
{\sum_{i \in \mathcal{D}_{j,bat}} w_i \cdot is\_legal\_delivery_i}
\]

For bowlers:

\[
Dot\%_{bowl,P,j} = 100 \times
\frac{\sum_{i \in \mathcal{D}_{j,bowl}} w_i \cdot is\_dot_i}
{\sum_{i \in \mathcal{D}_{j,bowl}} w_i \cdot is\_legal\_delivery_i}
\]

The batter improvement metric is:

\[
\Delta \%Dot_j = Dot\%_{base,j} - Dot\%_{P,j}
\]

Positive \(\Delta \%Dot\) means the batter reduced his dot-ball rate under pressure. The \(\Delta \%Dot\) personal baseline requires at least **120 legal balls** (all legal deliveries, not only balls faced). This 120-ball threshold is an approved exposure floor, not an empirically optimized cutoff.

### 8.7 Batter dismissal rate — Definition A is primary

#### Definitions

\[
BF_i = \mathbb{I}(extras\_type_i \ne \text{wide})
\]

\[
D_i = \mathbb{I}(is\_wicket_i \land dismissed\_player\_id_i = striker\_id_i \land dismissal\_type_i \ne \text{Retire Out})
\]

**Definition A — all legitimate striker dismissals (primary):**

\[
DR_A = 100 \times
\frac{\sum_i w_i D_i}{\sum_i w_i BF_i}
\]

**Definition B — wide-delivery dismissals removed from the numerator (sensitivity only):**

\[
DR_B = 100 \times
\frac{\sum_i w_i D_i \mathbb{I}(extras\_type_i \ne \text{wide})}
{\sum_i w_i BF_i}
\]

The balls-faced denominator is unchanged in both definitions. Definition A includes wide-delivery dismissals even though the wide delivery contributes zero to the denominator. This is the approved numerator/denominator asymmetry.

#### Wide-dismissal counts

| Scope | T20 Stump | T20 RunOut | T20I Stump | T20I RunOut | Total |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Full completed non-Super-Over | 15 | 4 | 10 | 5 | **34** |
| Batter pressure set \(P_{bat}\ge60\) | 7 | 2 | 7 | 4 | **20** |
| Outside pressure | 8 | 2 | 3 | 1 | **14** |

All 34 are in completed non-Super-Over data; none are in interrupted or Super Over files. Every affected pressure record has exactly one wide striker dismissal. The 20 pressure dismissals enter the Definition A numerator with zero balls-faced exposure.

#### Player-level impact for records with a personal baseline

\(\Delta DR = DR_{base} - DR_P\). Removing a dismissal raises \(\Delta DR\), so Definition B improves the affected batter's wicket-preservation score. The table shows the resulting \(\Delta z\) and the 10% composite contribution.

| Format | Batter | Baseline BF | \(DR_{base}\%\) | \(\Delta DR_A\) pp | \(\Delta DR_B\) pp | Shrunk A | Shrunk B | \(\Delta z\) | \(0.10\Delta z\) | Eligible |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| T20 | Ajinkya Rahane | 908 | 4.295 | -8.624 | -7.317 | -5.904 | -5.010 | +0.500 | **+0.0500** | Yes |
| T20 | Robin Uthappa | 143 | 6.993 | +3.555 | +6.993 | +1.265 | +2.488 | +0.828 | +0.0828 | No |
| T20 | M Shahrukh Khan | 126 | 7.937 | +0.389 | +0.742 | +0.328 | +0.625 | +0.198 | +0.0198 | Yes |
| T20 | Krunal Pandya | 306 | 3.922 | -3.199 | -2.887 | -2.771 | -2.501 | +0.132 | +0.0132 | Yes |
| T20 | Shubman Gill | 1883 | 3.186 | -1.371 | -0.672 | -1.086 | -0.533 | +0.347 | +0.0347 | Yes |
| T20 | Pathum Nissanka | 174 | 5.172 | -86.040 | +5.172 | -1.687 | +0.101 | +1.159 | +0.1159 | No |
| T20 | Abishek Porel | 381 | 4.987 | -2.603 | -2.087 | -1.872 | -1.501 | +0.213 | +0.0213 | Yes |
| T20I | Najibullah Zadran | 123 | 4.065 | -1.568 | -1.099 | -1.222 | -0.856 | +0.221 | +0.0221 | Yes |
| T20I | Ibrahim Zadran | 895 | 3.352 | +0.404 | +0.840 | +0.326 | +0.679 | +0.211 | +0.0211 | Yes |

Summary:

- **20** affected records; **10** eligible; **7** eligible records also have a 120-ball baseline and a computable primary composite.
- For those 7, Definition B would raise the composite by a mean of **+0.0260**, with a maximum of **+0.0500** for Rahane.
- Three eligible records — Abdul Samad, Shaheen Afridi, Shamim Hossain — lack the 120-ball baseline and are `BASELINE_INSUFFICIENT` under the primary rule.
- Ten affected records are ineligible and cannot enter the final ranking.

#### Reference populations for \(\Delta DR\)

| Format | n | Mean A | SD A | Mean B | SD B |
| :--- | ---: | ---: | ---: | ---: | ---: |
| T20 | 69 | -1.194059 | 1.538939 | -1.159482 | 1.503531 |
| T20I | 75 | -0.981492 | 1.608965 | -0.971921 | 1.613094 |

T20 values are unchanged. T20I values are the approved post-Q9 scoring-corpus values; the pre-Q9 T20I values are superseded.

#### Decision

**Definition A is primary.** It preserves legitimate dismissals, matches cricket attribution, and follows the same principle used for wide stumpings in the wicket-rate metric. Definition B is retained only as `DISMISSAL_RATE_WIDE_EXCLUDED` sensitivity. If a strictly per-ball dismissal hazard is ever required, it must be introduced as a new explicitly approved definition with a changed denominator, not as a silent correction.

### 8.8 Wicket rate — wide stumpings and \(N_{eff}\) Definition A

#### Definition

\[
WktRate_{P,j} =
\frac{\sum_{i \in \mathcal{D}_{j,bowl}} w_i \cdot is\_bowler\_wicket_i}
{\sum_{i \in \mathcal{D}_{j,bowl}} w_i \cdot is\_legal\_delivery_i}
\]

This is a proportion. For readability it may be multiplied by 100 and described as wickets per 100 legal balls; Z-scores use the proportion.

#### Wide stumpings

| Scope | Count |
| :--- | ---: |
| Full completed non-Super-Over | **25** |
| Bowler pressure set \(P_{bowl}\ge60\) | **6** |
| Outside pressure | **19** |

These 25 wide stumpings are **distinct from** the 34 wide striker dismissals in Section 8.7. The wicket-rate metric counts only `Stump`, not wide run-outs. Wide stumpings are legitimate bowler wickets and remain in the numerator; the denominator remains legal deliveries only. The asymmetry is retained and documented.

#### \(N_{eff}\) A versus B

- **A (primary):** \(N_{eff}\) is computed from **legal pressure deliveries only**.
- **B (sensitivity):** \(N_{eff}\) is computed from **all pressure deliveries**, including wides and no-balls.

The wicket numerator and legal-ball denominator are unchanged in both. The six affected bowler-format records are:

| Format | Bowler | \(N_{raw}\) | \(N_{legal}\) | \(M\) | Wide stump | \(N_{eff,A}\) | \(N_{eff,B}\) | \(\lambda_A\) | \(\lambda_B\) | Eligible | \(\Delta Z_{comp}\) (B−A) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: | ---: |
| T20 | Ravichandran Ashwin | 309 | 292 | 25 | 1 | 279.880 | 280.859 | 0.848430 | 0.848878 | Yes | -0.000005 |
| T20 | Karn Sharma | 77 | 75 | 6 | 1 | 73.117 | 74.116 | 0.593883 | 0.597151 | No | +0.000045 |
| T20I | Shakib Al Hasan | 79 | 78 | 8 | 1 | 73.024 | 73.996 | 0.593574 | 0.596761 | No | -0.000668 |
| T20I | Mohammad Nawaz | 202 | 196 | 18 | 1 | 186.301 | 187.257 | 0.788405 | 0.789258 | Yes | **+0.000165** |
| T20I | Sharafuddin Ashraf | 21 | 20 | 2 | 1 | 19.520 | 20.365 | 0.280785 | 0.289417 | No | +0.001736 |
| T20I | Matthew Humphreys | 92 | 89 | 8 | 1 | 85.376 | 86.284 | 0.630659 | 0.633119 | No | -0.000869 |

Only **Ashwin** and **Nawaz** are eligible affected records. The maximum eligible composite change is **0.000165**. Across all six affected records the maximum absolute change is 0.001736; among all eligible records it is 0.000165.

#### Peer means and reference populations

| Format | \(\mu_{peer}\) (raw WktRate) | Bowlers with \(\ge1\) legal pressure ball | Reference n | Mean | SD |
| :--- | ---: | ---: | ---: | ---: | ---: |
| T20 | 0.054911994 | 226 | 97 | 0.055020506 | 0.014290505 |
| T20I | 0.060033137 | 402 | 127 | 0.061824828 | 0.016235679 |

T20 values are unchanged. T20I values are the approved post-Q9 scoring-corpus values; the pre-Q9 T20I values are superseded. The Definition B reference moments are virtually identical.

**Decision:** retain **A**. Legal-delivery-only \(N_{eff}\) is the primary shrinkage denominator; all wide stumpings stay in the numerator; the legal-ball denominator stays. Definition B is `WKT_RATE_NEFF_ALL_DELIVERIES` sensitivity only.

### 8.9 Bowler boundary-conceded rate — `other` treatments

The bowler boundary-conceded rate is:

\[
BoundaryConcededRate_{P,j} = 100 \times
\frac{\sum_{i \in \mathcal{D}_{j,bowl}} w_i \cdot \mathbb{I}(is\_four_i \lor is\_six_i)}
{\sum_{i \in \mathcal{D}_{j,bowl}} w_i \cdot is\_legal\_delivery_i}
\]

The numerator counts batter-scored boundaries, including boundaries off overstep and provisional `other` deliveries. The denominator is legal deliveries only. This is a deliberate event-count asymmetry: a boundary off a no-ball is a real run-concession event even though the delivery is re-bowled.

#### Pressure-set scope — scoring corpus (191,963)

| Quantity | Scoring corpus | Audit reference |
| :--- | ---: | ---: |
| Bowler pressure rows \(P_{bowl}\ge60\) | **48,097** | 48,167 |
| Legal pressure deliveries | **45,769** | 45,837 |
| Non-legal pressure deliveries | **2,328** | 2,330 |
| Weighted legal denominator | **30,021.669303** | 30,057.770551 |

The scoring corpus is the operational population. The audit reference is shown because Q10's original approval recorded the boundary counts on the 192,056-row audit corpus. Match 48610's excluded chase contains **zero** `other` rows, so the `other` treatment itself is unaffected by Q9; the count difference is entirely non-`other` boundaries.

#### Boundary counts and weighted numerators — scoring corpus

| Extras type | Boundaries | Weighted numerator |
| :--- | ---: | ---: |
| Legal (`none`) | 9,756 | 6,547.268516 |
| Overstep | 34 | 24.077759 |
| `other` | 26 | 17.718495 |
| **All** | **9,816** | **6,589.064771** |

#### Q10 treatment definition and corpus-specific counts

The treatment is defined by the **rule**, not by a single corpus count:

- **Legal only:** excludes overstep and `other`.
- **Legal + overstep:** includes overstep, excludes `other`.
- **Legal + overstep + `other`:** includes all extras; this is the provisional primary rule.

| Treatment | Audit count (192,056) | Audit rate | Scoring count (191,963) | Scoring rate | Status |
| :--- | ---: | ---: | ---: | ---: | :--- |
| Legal only | 9,767 | **21.799812%** | 9,756 | **21.808476%** | Fully verified core |
| Legal + overstep | 9,801 | **21.879917%** | 9,790 | **21.888677%** | Conservative verified core |
| Legal + overstep + `other` | 9,827 | **21.938865%** | 9,816 | **21.947696%** | **Provisional primary** |

Audit weighted numerators are 6,552.537349 / 6,576.615108 / 6,594.333604 on the audit denominator 30,057.770551. Scoring weighted numerators are 6,547.268516 / 6,571.346275 / 6,589.064771 on the scoring denominator 30,021.669303. In both corpora, all three treatments use the same denominator within that corpus.

Format-specific provisional rates on the scoring corpus:

| Format | Legal only | Legal + overstep | Legal + overstep + `other` |
| :--- | ---: | ---: | ---: |
| T20 | 23.084362% | 23.144948% | 23.224193% |
| T20I | 20.698912% | 20.796171% | 20.837601% |

T20 values are unchanged. T20I values are post-Q9; the audit-corpus T20I rates are 20.685218% / 20.782260% / 20.823597%.

#### `other` pressure-set contents

| Quantity | Value |
| :--- | ---: |
| `other` pressure deliveries \(P_{bowl}\ge60\) | **88** |
| Batter runs | **139** |
| Extras runs | **104** |
| Boundaries | **26** |
| Weighted extras | **74.467115** |
| Weighted batter runs | **96.670587** |

These contents are identical in the audit and scoring corpora because Match 48610's excluded chase has zero `other` rows.

**Decision:** the primary bowler boundary-conceded metric uses the provisional **all-extras** rule, explicitly labelled `PROVISIONAL_OTHER`. Its operational scoring-corpus numerator is **9,816**; Q10's **9,827** remains the audit-corpus expression of the same rule. The verified-core sensitivities are **9,790** (scoring) / **9,801** (audit), and the legal-only sensitivities are **9,756** (scoring) / **9,767** (audit). No result may be described as fully verified while `other` remains unresolved.

### 8.10 `other` extras — reconciliation and unresolved classification

The selected cleaned scope contains **260** `other` deliveries. They reconcile exactly as:

| Cohort | Count |
| :--- | ---: |
| Completed non-Super-Over — audit and scoring corpora (`delivery_pressure_features.csv`) | **256** |
| Interrupted / no-result (`interrupted_delivery_features.csv`) | **3** |
| Super Over (`super_over_delivery_features.csv`) | **1** |
| **Total selected** | **260** |

Match 48610's excluded chase contains **zero** `other` rows, so the 256 completed non-Super-Over count is identical in the 192,056-row audit corpus and the 191,963-row scoring corpus. Under the exact final-eligibility rule, `other` affects **38 batter records / 34 players** and **40 bowler records / 37 players**; these are the ranking-eligible records whose `other`-dependent metrics can shift under reclassification.

The four out-of-cohort rows are:

| Match | Innings | Ball | Cohort | Batter runs | Extras | Boundary |
| ---: | ---: | ---: | :--- | ---: | ---: | :---: |
| 15546 | 1 | 74 | Interrupted | 4 | 1 | Yes |
| 39985 | 1 | 103 | Interrupted | 0 | 1 | No |
| 40725 | 3 | 4 | Super Over | 4 | 1 | Yes |
| 45908 | 1 | 25 | Interrupted | 0 | 1 | No |

**The classification of `other` remains `UNRESOLVED`.** The working treatment is provisional and no-ball-like:

- Non-legal delivery.
- Batter credited with balls faced and batter runs.
- Bowler charged batter runs plus extras.
- Batter-scored boundaries counted provisionally.
- Not a dot, because the delivery is non-legal.
- Excluded from the legal-ball wicket-rate denominator.

Because the classification is unresolved, the following are mandatory limitations: batter balls-faced totals, bowler economy, boundary-conceded rates, dot rates, and legal-ball denominators can all shift if `other` is reclassified. The approved boundary-treatment comparison is defined by rule; the operational scoring-corpus counts are **9,816 / 9,790 / 9,756**, with audit-corpus references **9,827 / 9,801 / 9,767**. A separate mandatory sensitivity treats `other` as a legal delivery for economy and dot-ball metrics, labelled `OTHER_AS_LEGAL`; it is not the primary treatment. No other boundary treatment comparison is approved.

---

## 9. Player Reliability Framework and Metric Decomposition

### 9.1 Metric decomposition and weights

Metrics are partitioned into **ceiling execution capacity** (absolute rate under pressure) and **clutch resilience** (delta over the player's own non-pressure baseline). This prevents double-counting absolute skill and pressure improvement.

#### A. Batter performance metrics — total 100%

| Metric | Weight | Definition | Direction |
| :--- | ---: | :--- | :--- |
| \(\Delta SR\) | **30%** | \(SR_P - SR_{base}\) | Positive better |
| \(\widehat{SR}_P\) | **25%** | Shrunk absolute pressure strike rate | Positive better |
| \(Boundary\%_P\) | **20%** | Batter-scored boundaries per ball faced under pressure | Positive better |
| \(\Delta \%Dot\) | **15%** | \(Dot\%_{base} - Dot\%_P\) | Positive better |
| \(\Delta DismissalRate\) | **10%** | \(DR_{base} - DR_P\) | Positive better |

#### B. Bowler performance metrics — total 100%

| Metric | Weight | Definition | Direction |
| :--- | ---: | :--- | :--- |
| \(\Delta Econ\) | **30%** | \(Econ_{base} - Econ_P\) | Positive better |
| \(\widehat{Econ}_P\) | **25%** | Shrunk absolute pressure economy (inverted in composite) | Lower better |
| \(WktRate_P\) | **20%** | Bowler-credited wickets per legal ball under pressure | Positive better |
| \(Dot\%_{bowl,P}\) | **15%** | Dot balls per legal ball under pressure | Positive better |
| \(BoundaryConcededRate_P\) | **10%** | Batter boundaries conceded per legal ball under pressure (inverted in composite) | Lower better |

The weights are identical **30 / 25 / 20 / 15 / 10** for both composites and sum to 100%.

### 9.2 Composite equations

#### Batter composite

\[
Z^{bat}_{comp,j} =
0.30\,Z(\Delta SR_j)
+ 0.25\,Z(SR_{P,j})
+ 0.20\,Z(Boundary\%_{P,j})
+ 0.15\,Z(\Delta \%Dot_j)
+ 0.10\,Z(\Delta DR_j)
\]

#### Bowler composite

\[
Z^{bowl}_{comp,j} =
0.30\,Z(\Delta Econ_j)
- 0.25\,Z(Econ_{P,j})
+ 0.20\,Z(WktRate_{P,j})
+ 0.15\,Z(Dot\%_{bowl,P,j})
- 0.10\,Z(BoundaryConcededRate_{P,j})
\]

The negative signs on \(Econ_P\) and \(BoundaryConcededRate_P\) are explicit because lower values are better. After those signs, every term in both composites is positive-better.

### 9.3 Sign conventions and delta definitions

\[
\Delta SR = SR_P - SR_{base}
\]

\[
\Delta \%Dot = Dot\%_{base} - Dot\%_P
\]

\[
\Delta DismissalRate = DR_{base} - DR_P
\]

\[
\Delta Econ = Econ_{base} - Econ_P
\]

Positive values mean better performance for every delta. \(P_{bat}\) and \(P_{bowl}\) are not performance metrics and are never added to these composites.

### 9.4 Correlation evidence — pairs unresolved

Three pairwise correlations among candidate metrics were estimated at:

\[
r = \mathbf{0.4778}, \qquad r = \mathbf{0.5233}, \qquad r = \mathbf{-0.692}
\]

The exact metric pairs behind these three values could not be reconstructed from the available audit trail. Their identities are therefore **`UNRESOLVED`**. Consequently:

- No independence claim is made for any pair of metrics.
- No weight is changed on the basis of these correlations.
- The previous claim of \(r = 0.384\) between \(\widehat{SR}_P\) and \(\Delta SR\) is **withdrawn**; it is not part of the approved evidence base.
- The approved 30/25/20/15/10 weights stand unchanged.

---

## 10. Delivery Weighting, Effective Sample Size, Shrinkage, and Eligibility

### 10.1 Delivery severity weights

Each delivery with \(P_i \ge 60.0\) receives:

\[
w_i = \left(\frac{P_i}{100.0}\right)^2
\]

Deliveries below the pressure cutoff receive \(w_i = 0\) and do not enter the pressure metric. The cutoff is 60.0 for the primary analysis; 55 and 65 are sensitivity values only.

### 10.2 Metric aggregation formulas

For a player-format record \(j\), with \(\mathcal{D}_{j,bat}\) or \(\mathcal{D}_{j,bowl}\) the relevant pressure set:

\[
SR_{P,j} = 100 \times
\frac{\sum_i w_i \cdot batter\_runs_i}
{\sum_i w_i \cdot BF_i}
\]

\[
Econ_{P,j} = 6.0 \times
\frac{\sum_i w_i \cdot bowler\_runs_i}
{\sum_i w_i \cdot is\_legal\_delivery_i}
\]

\[
WktRate_{P,j} =
\frac{\sum_i w_i \cdot is\_bowler\_wicket_i}
{\sum_i w_i \cdot is\_legal\_delivery_i}
\]

\[
Dot\%_{P,j} = 100 \times
\frac{\sum_i w_i \cdot is\_dot_i}
{\sum_i w_i \cdot is\_legal\_delivery_i}
\]

\[
Boundary\%_{P,j} = 100 \times
\frac{\sum_i w_i \cdot \mathbb{I}(is\_four_i \lor is\_six_i)}
{\sum_i w_i \cdot BF_i}
\]

\[
BoundaryConcededRate_{P,j} = 100 \times
\frac{\sum_i w_i \cdot \mathbb{I}(is\_four_i \lor is\_six_i)}
{\sum_i w_i \cdot is\_legal\_delivery_i}
\]

\[
DR_{P,j} = 100 \times
\frac{\sum_i w_i \cdot D_i}
{\sum_i w_i \cdot BF_i}
\]

All denominators must be strictly positive. A zero denominator yields an undefined metric and an `INSUFFICIENT_SAMPLE` flag, not a zero.

### 10.3 \(N_{eff}\) definitions

#### Delivery-level \(N_{eff}\) — eligibility

\[
N_{eff,del} = \frac{\left(\sum_i w_i\right)^2}{\sum_i w_i^2}
\]

This is computed over **all pressure deliveries** in the player-format record, including non-legal deliveries. It measures exposure breadth and is the approved denominator for the eligibility gate.

#### Balls-faced-weighted \(N_{eff}\)

\[
N_{eff,BF} = \frac{\left(\sum_i w_i BF_i\right)^2}{\sum_i (w_i BF_i)^2}
\]

Used for \(SR_P\), \(\Delta SR\), \(Boundary\%_P\), and \(\Delta DismissalRate\).

#### Legal-delivery-weighted \(N_{eff}\)

\[
N_{eff,legal} = \frac{\left(\sum_i w_i \cdot is\_legal\_delivery_i\right)^2}
{\sum_i (w_i \cdot is\_legal\_delivery_i)^2}
\]

Used for \(Econ_P\), \(\Delta Econ\), \(WktRate_P\) under Definition A, \(Dot\%_{bowl,P}\), and \(BoundaryConcededRate_P\).

For \(\Delta \%Dot\), use the legal-delivery-weighted form because dot balls are defined only on legal deliveries.

For \(WktRate_P\) under Definition B, use \(N_{eff,del}\) as the sensitivity denominator.

### 10.4 Metric-specific versus eligibility \(N_{eff}\)

The approved separation is:

- **Metric-specific \(N_{eff}\)** is used for **shrinkage** of each metric. The appropriate denominator depends on the metric (BF-weighted or legal-weighted).
- **Delivery-level \(N_{eff}\)** is used for the **eligibility gate**. It is not substituted into metric shrinkage.

Using a single \(N_{eff}\) everywhere would mix exposure breadth with metric-specific information content. The separation is retained.

### 10.5 Kish caveat

Kish's formula assumes independent weighted observations. Deliveries within a player's match are correlated: the same batter faces consecutive balls, the same bowler bowls consecutive balls, and match state is autocorrelated. \(N_{eff}\) therefore **overstates the number of independent observations**. It is a variance-inflation diagnostic, not a literal independent sample count.

The approved thresholds \(N_{eff}\ge35\) and \(K=50\) are retained despite this caveat. The caveat is a documented limitation, not a reason to change the gate.

### 10.6 Empirical Bayes shrinkage

For absolute metrics:

\[
\widehat{M}_{j} =
\frac{N_{eff,j}}{N_{eff,j}+K}\,\cdot\,M_{P,j}
+
\frac{K}{N_{eff,j}+K}\,\cdot\,\mu_{peer}
\]

For delta metrics:

\[
\widehat{\Delta M}_{j} =
\frac{N_{eff,j}}{N_{eff,j}+K}\,\cdot\,\Delta M_j
+
\frac{K}{N_{eff,j}+K}\,\cdot\,0.0
\]

Where:

- \(K = 50.0\).
- \(\mu_{peer}\) is the format-specific peer mean.
- Delta metrics shrink toward zero improvement.

#### \(\mu_{peer}\) definition

\(\mu_{peer}\) is the **unweighted mean across players** within a format, computed over players with at least one valid pressure opportunity for that metric. No \(N_{raw}\), \(N_{eff}\), baseline, or \(M\) gate is applied. No cross-format pooling is permitted. The opportunity denominator is balls faced for \(SR_P\) and \(Boundary\%_P\), and legal pressure balls for the bowler metrics.

#### \(\mu_{peer}\) values — scoring corpus (191,963)

| Metric | IPL / T20 | T20I | Peer pool |
| :--- | ---: | ---: | :--- |
| \(WktRate_P\) | **0.054911994** | **0.060033137** | 226 T20 bowlers; 402 T20I bowlers with \(\ge1\) legal pressure ball |
| \(Boundary\%_P\) | **15.242915** | **12.937251** | 303 T20 batters; 603 T20I batters |
| \(Boundary\%_P\) runs proxy | 15.251816 | 12.946251 | Same batter pools |
| \(SR_P\) | **123.019515** | **113.401880** | 303 T20 batters; 603 T20I batters |
| \(Econ_P\) | **11.208029** | **9.621940** | 226 T20 bowlers; 402 T20I bowlers |
| \(Dot\%_{bowl,P}\) | **26.278545** | **30.560287** | 226 T20 bowlers; 402 T20I bowlers |
| \(BoundaryConcededRate_P\) | **25.821922** | **20.082100** | 226 T20 bowlers; 402 T20I bowlers |

T20 values are unchanged. T20I values are the approved post-Q9 scoring-corpus values. All values are format-specific; no cross-format pooling of \(\mu_{peer}\) is allowed.

### 10.7 Personal baselines

Personal baselines are computed from **non-pressure deliveries** (\(P<60\)) in the same format.

| Baseline | Minimum exposure | Approved status |
| :--- | :--- | :--- |
| Batter \(SR_{base}\), \(DR_{base}\) | **120 balls faced** | Approved dual gate (Q4) |
| Batter \(Dot\%_{base}\) | **120 legal balls** | Approved dual gate (Q4); both gates required |
| Bowler \(Econ_{base}\), \(Dot\%_{base}\), \(BoundaryConcededRate_{base}\) | **120 legal balls bowled** | Approved (Q3); legal-ball denominator; no peer fallback |

The batter baseline is a **dual gate**: 120 balls faced for \(SR_{base}\) and \(DR_{base}\), and 120 legal balls for \(Dot\%_{base}\). **Both** must be satisfied. Each metric uses its own denominator: balls faced for \(SR_{base}\) and \(DR_{base}\); legal deliveries for \(Dot\%_{base}\). The bowler baseline is **120 legal balls bowled**, with \(Econ_{base} = 6 \sum bowler\_runs / \sum legal\) and legal deliveries for all three baseline metrics. The 120-ball floors are approved exposure anchors; they are not empirically optimized cutoffs.

If the baseline exposure is insufficient:

- The record is flagged `BASELINE_INSUFFICIENT`.
- The primary composite is not computed.
- The player may still appear in descriptive tables, but not in the primary ranking.

No peer fallback is permitted, and no replacement baseline is substituted silently.

### 10.8 Format set, \(M_{role}\), and final eligibility gate

For player \(j\) in role \(r\), define the role-specific pressure set and the format set:

\[
D_{j,f,r} = \{i : \text{player } j \text{ in role } r,\ \text{format } f,\ P_{r,i} \ge 60.0\}
\]

\[
N_{raw,j,f,r} = |D_{j,f,r}|
\]

\[
N_{eff,del,j,f,r} = \frac{\left(\sum_{i \in D_{j,f,r}} w_i\right)^2}{\sum_{i \in D_{j,f,r}} w_i^2}
\]

\[
F_{j,r} = \left\{ f :\ N_{raw,j,f,r} \ge 75 \ \land\ N_{eff,del,j,f,r} \ge 35 \ \land\ baseline\_ok_{j,f,r} \ \land\ \text{all five metric denominators} > 0 \ \land\ Z_{comp,j,f,r}\ \text{finite} \right\}
\]

Match breadth is calculated **after** \(F_{j,r}\) is formed, using only the formats that remain in \(F_{j,r}\):

\[
M_{role,j,r} = \left| \bigcup_{f \in F_{j,r}} \left\{ match\_id_i : i \in D_{j,f,r} \right\} \right|
= \sum_{f \in F_{j,r}} M_{j,f,r}
\]

The equality holds because IPL/T20 and T20I are disjoint formats; each match is counted once. Matches from formats excluded by baseline, zero denominators, or other format-level failures do **not** count.

**Final ranking eligibility is exactly:**

\[
\text{ranking-eligible}_{j,r} =
\bigl(F_{j,r} \neq \varnothing\bigr)
\;\land\;
\bigl(M_{role,j,r} \ge 10\bigr)
\]

The operational rules are:

- \(N_{raw}\) and \(N_{eff,del}\) are evaluated **per format record**.
- \(M_{role}\) is evaluated **only across formats in \(F_{j,r}\)**. Formats dropped from \(F_{j,r}\) do not contribute matches.
- A player with \(F_{j,r} \neq \varnothing\) but \(M_{role,j,r} < 10\) is flagged `M_BREADTH_INSUFFICIENT` and **must not enter the final ranking**. The player may remain in descriptive tables and in the calibration population.
- A player with \(F_{j,r} = \varnothing\) is excluded from that role and flagged `INSUFFICIENT_SAMPLE` or `BASELINE_INSUFFICIENT` as applicable.
- The calibration population is **exempt** from the \(M \ge 10\) gate.

Flag precedence is:

```text
INVALID
> BASELINE_INSUFFICIENT
> INSUFFICIENT_SAMPLE
> M_BREADTH_INSUFFICIENT
> RANKING_ELIGIBLE
```

Approved Stage 4.2 counts on the 191,963-delivery scoring corpus:

| Scope | Batter | Bowler | Both roles |
| :--- | ---: | ---: | ---: |
| \(F_{j,r}\) non-empty — composite-ready records | **144** | **209** | — |
| \(F_{j,r}\) non-empty — composite-ready players | **122** | **173** | — |
| Excluded solely by \(M_{role} < 10\) — players | **21** | **32** | — |
| Final ranking-eligible records | **123** | **177** | — |
| Final ranking-eligible players | **101** | **141** | **23** |
| Calibration population (\(M \ge 10\) not applied) | **122** | **173** | — |
| \(M_{all}\) comparison only — records / players | 125 / 103 | 182 / 146 | 24 |

The \(M_{all}\) comparison counts all role pressure matches, including matches from formats dropped from \(F_{j,r}\). It is a documented comparison and sensitivity only; it is **not** the primary eligibility rule. Per-format \(M \ge 10\) is likewise a sensitivity check only. The thresholds \(N_{raw}=75\), \(N_{eff,del}=35\), and \(M=10\) are unchanged.

---

## 11. Standardization, Cross-Format Ranking, and Reliability Score

### 11.1 Format-specific standardization

Every shrunk metric is standardized strictly within its format, **separately for each role**:

\[
Z_{m,j,f,r} = \frac{\widehat{M}_{m,j,f,r} - \mu^{ref}_{m,f,r}}{\sigma^{ref}_{m,f,r}}
\]

Where:

- \(\widehat{M}_{m,j,f,r}\) is the shrunk metric for player \(j\), metric \(m\), format \(f\), role \(r\).
- \(\mu^{ref}_{m,f,r}\) and \(\sigma^{ref}_{m,f,r}\) are the format- and role-specific reference mean and standard deviation.
- No raw metric is pooled across formats or roles before standardization.

### 11.2 Reference population and moments

The reference population for each metric and role is:

- Players with \(N_{raw}\ge75\) and \(N_{eff,del}\ge35\) in that format.
- All five metric denominators positive and finite \(Z_{comp}\).
- Baseline available where the metric is a delta metric.
- The \(M\ge10\) match-breadth gate is **not applied** to the reference population. Applying it here would make the standardization population depend on the final ranking gate.
- Reference moments are computed on the **shrunk metric scale** with **population SD** (\(\mathrm{ddof}=0\)). No cross-format or cross-role pooling is permitted.

Approved reference moments on the 191,963-delivery scoring corpus:

| Role | Metric | Format | n | Mean | SD |
| :--- | :--- | :--- | ---: | ---: | ---: |
| Batter | \(\Delta SR\) | T20 | 69 | 6.947364 | 12.751996 |
| Batter | \(\Delta SR\) | T20I | 75 | 8.948109 | 17.481057 |
| Batter | \(SR_P\) | T20 | 101 | 143.359818 | 16.348827 |
| Batter | \(SR_P\) | T20I | 142 | 132.253244 | 16.828045 |
| Batter | \(Boundary\%_P\) (flags) | T20 | 101 | 18.412502 | 3.079949 |
| Batter | \(Boundary\%_P\) (flags) | T20I | 142 | 16.005504 | 3.335999 |
| Batter | \(\Delta \%Dot\) | T20 | 69 | 3.839264 | 4.399535 |
| Batter | \(\Delta \%Dot\) | T20I | 75 | 3.602711 | 5.531160 |
| Batter | \(\Delta DismissalRate\) (A) | T20 | 69 | -1.194059 | 1.538939 |
| Batter | \(\Delta DismissalRate\) (A) | T20I | 75 | -0.981492 | 1.608965 |
| Bowler | \(\Delta Econ\) | T20 | 94 | -1.076418 | 0.944761 |
| Bowler | \(\Delta Econ\) | T20I | 115 | -1.025055 | 0.856238 |
| Bowler | \(Econ_P\) | T20 | 97 | 10.582169 | 1.018373 |
| Bowler | \(Econ_P\) | T20I | 127 | 9.681679 | 0.907976 |
| Bowler | \(WktRate_P\) (A) | T20 | 97 | 0.055020506 | 0.014290505 |
| Bowler | \(WktRate_P\) (A) | T20I | 127 | 0.061824828 | 0.016235679 |
| Bowler | \(Dot\%_{bowl,P}\) | T20 | 97 | 27.652433 | 3.287661 |
| Bowler | \(Dot\%_{bowl,P}\) | T20I | 127 | 30.408426 | 3.688606 |
| Bowler | \(BoundaryConcededRate_P\) | T20 | 97 | 24.041620 | 4.029733 |
| Bowler | \(BoundaryConcededRate_P\) | T20I | 127 | 20.760668 | 3.148889 |

T20 values are unchanged. T20I values are the approved post-Q9 values and supersede the pre-Q9 table. The Definition B wicket-rate moments are virtually identical. The runs-proxy boundary moments are reported in Section 8.5.

### 11.3 Composite Z and one player-level entry per role

For each role \(r\), the per-format composite is:

\[
Z_{comp,j,f,r} =
\sum_{m=1}^{5} w_m Z_{m,j,f,r}
\]

using the approved 30/25/20/15/10 weights and the signs in Section 9.2.

The final ranking has **one row per player per role**, not one row per player-format and not a combined all-rounder row. All-rounders appear independently in the batter and bowler rankings when they satisfy that role's gates. Let \(\mathcal{F}_{j,r}\) be the set of formats in which player \(j\) passes the format-level conditions for role \(r\) (Section 10.8).

#### Primary: equal format weighting

\[
Z^{*}_{comp,j,r} =
\begin{cases}
Z_{comp,j,f,r} & |\mathcal{F}_{j,r}| = 1 \\
\frac{1}{2}Z_{comp,j,T20,r} + \frac{1}{2}Z_{comp,j,T20I,r} & |\mathcal{F}_{j,r}| = 2
\end{cases}
\]

Equal weighting is the **approved primary**. Format-specific Z-scores are already standardized, so equal weighting prevents a high-exposure format from dominating the player's cross-format score.

#### Sensitivity: \(N_{eff}\)-proportional weighting

\[
Z^{*}_{comp,j,r} =
\frac{\sum_{f \in \mathcal{F}_{j,r}} N_{eff,j,f,r} \, Z_{comp,j,f,r}}
{\sum_{f \in \mathcal{F}_{j,r}} N_{eff,j,f,r}}
\]

where \(N_{eff,j,f,r}\) is the delivery-level \(N_{eff}\) for the role-specific format record.

#### Optional sensitivity: capped \(N_{eff}\)-proportional weighting

\[
Z^{*}_{comp,j,r} =
\frac{\sum_{f \in \mathcal{F}_{j,r}} \min(N_{eff,j,f,r}, C) \, Z_{comp,j,f,r}}
{\sum_{f \in \mathcal{F}_{j,r}} \min(N_{eff,j,f,r}, C)}
\]

The cap \(C\) is required **only if this optional sensitivity is later performed**. No numeric cap value has been approved, and \(C\) is **not a primary implementation blocker**. If the optional analysis is run, \(C\) must be registered and recorded before any result is produced; otherwise the sensitivity is not reproducible. Equal format weighting remains the approved primary.

Only formats in \(\mathcal{F}_{j,r}\) enter the role-specific composite. After \(Z^{*}_{comp,j,r}\) is formed, \(M_{role,j,r}\ge10\) is applied as the separate final gate. A player with \(\mathcal{F}_{j,r}=\varnothing\) is excluded from that role. A player may be eligible in one role and not the other. **No combined all-rounder composite is produced in the primary analysis.**

### 11.4 Calibration population and constants

The calibration population is defined separately for each role:

- **One row per player per role**, not per player-format.
- For dual-format players, the equal-weight average of their eligible format composites.
- For one-format players, that single format composite.
- Dual-format players are counted **once**; one-format players are counted **once**.
- \(F_{j,r}\) must be non-empty.
- The \(M\ge10\) match-breadth gate is **not applied**. The calibration population therefore includes the **21 batter / 32 bowler** players excluded from the final ranking by \(M_{role}<10\).
- Moments use **population SD** (\(\mathrm{ddof}=0\)); the equal-weight format average is taken before computing the moments.

| Role | Calibration n | \(\mu_{Zcomp}\) | \(\sigma_{Zcomp}\) |
| :--- | ---: | ---: | ---: |
| Batter | **122** | **0.1036068081** | **0.6610638828** |
| Bowler | **173** | **0.0256919707** | **0.6655792246** |

These constants are computed on the **122 batter / 173 bowler** calibration population, **not** on the 101/141 final ranking population. Do not recompute them on the ranking-eligible subset. This population is used for reliability calibration and distribution checks. It does not re-estimate \(\gamma\); the slope remains fixed at 0.80.

### 11.5 Calibrated reliability score

\[
Z^{*}_{std,j,r} = \frac{Z^{*}_{comp,j,r} - \mu_{Zcomp,r}}{\sigma_{Zcomp,r}}
\]

\[
\text{Reliability}_{j,r} =
\frac{100.0}{1.0 + \exp\left(-\gamma \cdot Z^{*}_{std,j,r}\right)},
\qquad \gamma = 0.80
\]

The score is strictly bounded in \([0,100]\), monotonic in \(Z^{*}_{std}\), and centred at **50.0** when \(Z^{*}_{std}=0\) (equivalently, when \(Z^{*}_{comp}=\mu_{Zcomp}\)). It is a reliability index, not a probability.

| Performance category | \(Z^{*}_{std}\) | Reliability | Interpretation |
| :--- | ---: | ---: | :--- |
| Generational outlier | +2.50 | **88.1** | Transcendent pressure performer |
| Elite tournament finisher | +2.00 | **83.2** | Top-tier clutch execution |
| Strong dependable performer | +1.00 | **69.0** | Consistently outperforms baseline under stress |
| Above average | +0.50 | **59.9** | Positive clutch delta |
| Calibration-population mean | 0.00 | **50.0** | At the calibration mean |
| Below average | -0.50 | **40.1** | Slight decline under pressure |
| Vulnerable under pressure | -1.00 | **31.0** | Material drop under stress |
| Severe pressure collapse | -2.00 | **16.8** | Chronic negative clutch delta |
| Extreme lower tail | -3.00 | **8.3** | Extreme negative tail |
| Extreme upper tail | +3.00 | **91.7** | Extreme positive tail |

Calibrated reliability distributions:

| Role | n | Raw mean | Raw SD | Calibrated mean | Calibrated SD | Calibrated range |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| Batter | 122 | 51.957189 | 12.419869 | 50.025365 | 17.607254 | 9.120–85.170 |
| Bowler | 173 | 50.525126 | 12.570009 | 50.119097 | 17.771236 | 11.471–87.823 |

The previously stated \(\pm1\) standard deviation mapping \([31.0,69.0]\) applies to the calibrated \(Z^{*}_{std}\) scale.

### 11.6 Ranking order and tie-break

For each role, sort **only** players with \(\text{ranking-eligible}_{j,r}=\text{True}\) by:

1. \(Z^{*}_{comp,j,r}\) descending.
2. \(\sum_{f \in F_{j,r}} N_{eff,del,j,f,r}\) descending.
3. \(M_{role,j,r}\) descending.
4. \(\sum_{f \in F_{j,r}} N_{raw,j,f,r}\) descending.
5. `player_id` ascending.

No ineligible player enters the sort. The order is deterministic and contains no random component.

### 11.7 Ranking universe and season pooling

The primary ranking universe is **all ranking-eligible players** in the 812-match, 191,963-delivery scoring corpus, separately for batter and bowler. No team, auction-status, or shortlist pre-filter is applied to the primary ranking.

The RR/auction shortlist is a **separate view** built from the primary rankings. It does not change eligibility, standardization, calibration, or the primary order.

Season pooling is **equal per delivery**: every qualifying pressure delivery carries its existing weight, and seasons are pooled at the delivery level, so a season with more qualifying deliveries contributes proportionally more. Mandatory sensitivities are:

- **Season-equal:** each season contributes equal weight regardless of delivery volume.
- **2024–2026 only:** restrict to the most recent three seasons.

The primary is neither season-equal nor restricted to 2024–2026.

---

## 12. Special Cases and Edge-Case Protocols

### 12.1 Match 48610 — unresolved DLS target

Match 48610 contains **194** deliveries:

- **101** first-innings deliveries with `NOT_APPLICABLE`.
- **93** second-innings deliveries with `UNRESOLVED_TARGET`.

**Q9 primary treatment:** the **93 second-innings rows are excluded** from all primary pressure and personal-baseline calculations. The **101 first-innings rows are retained**. The operational scoring corpus is therefore **191,963 deliveries across 812 matches**. The excluded rows remain in the 192,056-row audit corpus only. Under the exact final-eligibility rule, the exclusion affects **5 batter records / 3 players** and **9 bowler records / 5 players**.

For the 93 excluded chase deliveries:

- `target_score`, `runs_required`, and `runs_required_raw` are **`NaN`**.
- `is_target_reached_before` is `False` for every row.
- There are **zero** post-target deliveries, because no target is defined.
- Chase pressure features are unavailable, and the rows contribute **no pressure or baseline exposure**.

**Sensitivity only:** the 93 rows may be evaluated with the first-innings resource-strain formulas (\(P_1\)) under the explicit label `MATCH_48610_P1_FALLBACK`. This is not the primary treatment and does not fabricate a target. The DLS provenance remains documented unresolved evidence; it is not silently treated as a verified chase.

### 12.2 Super Overs

There are **4** Super Over matches and **26** deliveries in `super_over_delivery_features.csv`. They are preserved in a dedicated artifact for exhibition analysis but **excluded from the 20-over tournament reliability rankings**. No claim is made that Super Over pressure equals 100; the standard pressure engine is not defined for the Super Over rules.

### 12.3 Interrupted / no-result matches

There are **25** interrupted matches and **1,932** deliveries in `interrupted_delivery_features.csv`. They are preserved for partial-match context but **excluded** from the **191,963-delivery primary scoring corpus**. The primary corpus therefore contains only completed match arcs.

### 12.4 Target provenance

| Provenance | Treatment |
| :--- | :--- |
| `STANDARD_TARGET` | Chase equations; target = first-innings total + 1 |
| `VERIFIED_REVISED_TARGET` | Chase equations; validated DLS revised target |
| `UNRESOLVED_TARGET` | Chase features `NaN`; Match 48610 second innings excluded from the primary scoring corpus (Q9); `MATCH_48610_P1_FALLBACK` sensitivity only |
| `NOT_APPLICABLE` | First-innings equations |

### 12.5 Invalid deliveries and zero denominators

- `balls_rem <= 0` → `INVALID`, exclude. Never clamp to 1.
- `max_balls <= 0` or missing → `INVALID`, exclude.
- Zero legal balls in a denominator → metric undefined, `INSUFFICIENT_SAMPLE`.
- Zero balls faced in a denominator → metric undefined, `INSUFFICIENT_SAMPLE`.

The current completed corpus has zero invalid `balls_rem` rows. The rules are retained for future data.

### 12.6 `other` extras

**260** selected `other` deliveries = **256** completed non-Super-Over + **3** interrupted + **1** Super Over. Classification is `UNRESOLVED`. The working treatment is provisional no-ball-like. The four out-of-cohort rows are listed in Section 8.10. Match 48610's excluded chase contains **zero** `other` rows, so the **256** count is identical in the 192,056-row audit corpus and the 191,963-row scoring corpus. The boundary treatment is defined by rule: operational scoring-corpus counts are **9,816** (all extras, provisional primary), **9,790** (legal + overstep, verified core), and **9,756** (legal only); the corresponding audit-corpus references are **9,827 / 9,801 / 9,767**.

### 12.7 Wide dismissals

- Batter dismissal rate uses **Definition A**: all legitimate striker dismissals, including wide-delivery dismissals, with the balls-faced denominator unchanged.
- Definition B, excluding wide-delivery dismissals from the numerator, is sensitivity only.
- Counts: **34** full completed wide striker dismissals; **20** in the batter pressure set; **14** outside.
- Wicket rate retains **25** wide stumpings in the numerator: **6** in the bowler pressure set; **19** outside.
- The two count systems are distinct and must not be conflated.

### 12.8 Boundary numerator

- Primary: source `is_four | is_six` flags.
- Sensitivity: `batter_runs in {4,6}` proxy, labelled `BOUNDARY_RUNS_PROXY`.
- Full-data difference: 34,733 flags vs 34,756 runs proxy (+23).
- Pressure difference: 11,012 flags vs 11,019 runs proxy (+7, all-run fours).
- No change to the 20% boundary weight.

### 12.9 Retire Out, non-striker run-outs, and obstructing the field

- **Retire Out** is excluded from the batter dismissal numerator. This exclusion is proposed, not fully verified against every source scorecard.
- **Non-striker run-outs** are excluded by the striker-dismissal definition.
- **Obstructing the field** is excluded from bowler-credited wickets.

### 12.10 Penalty, byes, and leg-byes

- Penalty runs are team extras and are never charged to the bowler.
- Byes and leg-byes are legal deliveries, count as balls faced, and are not charged to the bowler.
- Penalty rows follow the source legality flag; they are not a standard delivery event.

### 12.11 Rain-shortened matches

`max_balls` is match-specific. Phase boundaries are proportional. The horizon functions scale exactly. Scenario S8 and Worked Example WE5 demonstrate a 60-ball innings. No fixed 120-ball denominator is assumed.

### 12.12 Format scoring parity

IPL all-innings CRR is **9.3201**; T20I is **8.5516**. The gap is **+0.7685 RPO**. All metrics are standardized within format before cross-format pooling. The first-innings comparison values are 9.3749 and 8.6673; they are not the primary baseline.

---

## 13. Sensitivity and Validation Plan

### 13.1 Approved sensitivity grid

| Parameter | Primary | Sensitivity values |
| :--- | ---: | :--- |
| Pressure cutoff \(P\) | 60 | 55, 65 |
| Shrinkage constant \(K\) | 50 | 25, 100 |
| Raw pressure deliveries \(N_{raw}\) | 75 | 50, 100 |
| Rank stability target | — | Spearman \(\rho > 0.92\) across adjacent configurations |

### 13.2 Mandatory additional sensitivity analyses

1. **Wicket-rate \(N_{eff}\):** A (legal-delivery-only, primary) versus B (all-delivery).
2. **Batter dismissal rate:** A (all legitimate striker dismissals, primary) versus B (wide-delivery dismissals excluded).
3. **Batter boundary percentage:** source flags (primary) versus `BOUNDARY_RUNS_PROXY`.
4. **`other` boundary-conceded treatment:** all-extras rule (provisional primary; scoring 9,816 / audit 9,827), verified core (scoring 9,790 / audit 9,801), legal only (scoring 9,756 / audit 9,767).
5. **`other` extras classification:** provisional no-ball-like primary; mandatory `OTHER_AS_LEGAL` economy/dot-ball sensitivity; reclassification scenarios must be explicitly labelled.
6. **Cross-format weighting:** equal (primary); \(N_{eff}\)-proportional (required sensitivity); capped \(N_{eff}\)-proportional (**optional** sensitivity; \(C\) required only if performed).
7. **CRR baseline:** all-innings (primary) versus first-innings comparison values.
8. **Final eligibility / match breadth:** \(F_{j,r}\) non-empty **AND** \(M_{role,j,r}\ge10\) (primary); \(M_{all}\) comparison; per-format \(M\ge10\) sensitivity.
9. **\(N_{eff}\) scope:** legal-only versus all-delivery where the metric definition permits.
10. **Baseline exposure:** the approved batter dual gate (120 balls faced for \(SR_{base}\)/\(DR_{base}\); 120 legal balls for \(Dot\%_{base}\)) and the bowler 120-legal-ball rule are primary; any alternative must be pre-registered before execution.
11. **Match 48610:** exclude the 93 second-innings rows from pressure and baseline (primary); `MATCH_48610_P1_FALLBACK` sensitivity only.
12. **Season pooling:** equal per delivery (primary); season-equal and 2024–2026-only sensitivities.

### 13.3 Validation tests

1. **Boundary conformance:** \(0 \le P_{bat},P_{bowl},Reliability \le 100\).
2. **Monotonicity:** \(P_{bat}\) increases with required rate and wickets lost. \(P_{bowl,2}\) peaks at \(Surplus=0\) and declines with \(|Surplus|\); it is not globally monotonic in \(Surplus\).
3. **Contrast cases:**
   - S5: 42 off 6 with 6 wickets → \(P_{bat}>95\), \(P_{bowl}<5\).
   - S3: 6 off 6 with 1 wicket → \(P_{bowl}>90\).
   - WE6: 12 off 6 with 1 wicket → \(P_{bowl}>90\).
   - S8: 45 off 30 in a 10-over match → \(P_{bowl}>80\).
4. **Null safety:** zero unhandled `NaN` or `inf` across the **191,963** scored deliveries after the defined exclusions. The 192,056-row audit corpus still contains the 93 excluded Match 48610 chase rows.
5. **Determinism:** no randomness; identical inputs and constants reproduce identical tables and scores.
6. **Sensitivity stability:** target Spearman \(\rho > 0.92\) across adjacent configurations.
7. **Role separation:** batter and bowler rankings are produced independently; an all-rounder may appear in both; no combined all-rounder row exists in the primary.
8. **Eligibility conformance:** every ranked player has \(F_{j,r}\neq\varnothing\) and \(M_{role,j,r}\ge10\); no player with \(M_{role}<10\) appears in the final ranking; the calibration population is 122 batter / 173 bowler and includes the 21/32 players excluded by the final gate.
9. **Calibration conformance:** \(Z^{*}_{std}\) uses the approved per-role \(\mu_{Zcomp}\) / \(\sigma_{Zcomp}\); Reliability \(=100/(1+\exp(-0.80 Z^{*}_{std}))\) and is centred at 50 at the calibration mean.

### 13.4 Reproducibility

All calculations are deterministic functions of `data/processed/delivery_pressure_features.csv` and the constants in this document. The approved scoring reference corpus is **191,963 completed non-Super-Over deliveries across 812 matches**, after the Q9 exclusion of the 93 Match 48610 second-innings deliveries. The 192,056-row completed non-Super-Over audit corpus is retained for reconciliation. The auxiliary corpora are separately identified. No random seed is required.

---

## 14. Limitations and Unresolved Evidence

1. **`other` classification is unresolved.** The 260 selected rows reconcile to 256 completed + 3 interrupted + 1 Super Over, but the cricket meaning of `other` is not proven. All `other`-dependent results are provisional.
2. **Correlation pair identities are unresolved.** The values 0.4778, 0.5233, and -0.692 are retained, but the exact metric pairs are not reconstructed. No independence claim is made.
3. **Match 48610 DLS provenance remains unresolved.** The 93 second-innings rows are excluded from the primary scoring corpus; `MATCH_48610_P1_FALLBACK` is sensitivity only. No post-target rows exist.
4. **Batter dismissal-rate asymmetry.** Definition A includes 20 pressure wide-delivery dismissals with zero balls-faced exposure. The denominator remains unchanged by approval.
5. **Retire Out exclusion is proposed, not verified.**
6. **`bowler_runs` is derived, not native.** Wide, overstep, and provisional `other` deliveries are charged batter runs plus extras; byes, leg-byes, and penalties are not charged.
7. **Capped \(N_{eff}\)-proportional weighting is optional.** No numeric cap \(C\) is approved, but \(C\) is not required for primary implementation. It must be registered only if the optional capped-\(N_{eff}\) sensitivity is later performed. Calibration is fixed by the approved per-role \(\mu_{Zcomp}\) / \(\sigma_{Zcomp}\).
8. **The 120-ball baseline is approved but not empirically optimized.** The batter dual gate is 120 balls faced for \(SR_{base}\)/\(DR_{base}\) and 120 legal balls for \(Dot\%_{base}\); the bowler rule is 120 legal balls.
9. **Boundary flags are inferred as batter boundaries.** Every flag has `batter_runs` 4 or 6; 20 full-data fours and 3 full-data sixes lack flags and are inferred all-run events. No independent boundary-distance field exists.
10. **Wicket-rate wide-stumping asymmetry.** 25 wide stumpings are retained in the numerator; only 6 are in the bowler pressure set. The legal-ball denominator is unchanged.
11. **The `other` boundary-conceded primary is not fully verified.** Operational scoring-corpus counts are 9,816 (all extras, provisional primary), 9,790 (verified core), and 9,756 (legal only); audit-corpus references are 9,827 / 9,801 / 9,767.
12. **No rankings have been generated.** Player-level impacts are \(\Delta Z_{comp}\), not rank movements.
13. **Kish \(N_{eff}\) overstates independent information.** Deliveries within a player-match are correlated.
14. **Phase RPO values are informational only.** They are not inputs to any equation or weight.
15. **Super Overs and interrupted matches are excluded.** Their counts are preserved separately.
16. **First-innings CRR is a comparison, not the primary baseline.**
17. **Pressure scores are not performance scores.** Higher \(P_{bat}\) or \(P_{bowl}\) means more situational pressure, not better or worse player performance.
18. **Final ranking eligibility is \(F_{j,r}\) non-empty AND \(M_{role,j,r}\ge10\).** \(M_{all}\) and per-format \(M\ge10\) are sensitivity only.
19. **Calibration excludes the \(M\ge10\) gate.** This avoids circularity; the gate is applied only at final ranking admission.
20. **The previous \(r=0.384\) independence claim is withdrawn.** It is not part of the approved evidence.
21. **Role-specific rankings.** Batter and bowler rankings are independent; no combined all-rounder ranking is produced in the primary.
22. **Season pooling primary is equal per delivery.** Season-equal and 2024–2026-only are mandatory sensitivities.

---

## Appendix A. Approved Decision Register

### A.1 The 17 Stage 4 corrections

| # | Approved correction | Final treatment |
| ---: | :--- | :--- |
| 1 | All-innings CRR | IPL **9.3201**, T20I **8.5516**; primary |
| 2 | First-innings comparison CRR | IPL **9.3749**, T20I **8.6673**; comparison/sensitivity only |
| 3 | Wicket baseline | IPL **6.2624**, T20I **6.7867** |
| 4 | Bowling equation | Surplus-based Gaussian; `Tension + Threat` retired |
| 5 | Gaussian width | **\(\sigma_S = 12\) runs** |
| 6 | Binary trigger | `balls_rem <= 12`, `0 < runs_req <= 12`, `W_rem = 1` |
| 7 | Binary leverage | **\(Leverage_{binary} = 3.00\)** |
| 8 | Canonical scenarios | **8** scenarios, Section 6 |
| 9 | Worked examples | **6** examples, Section 7 |
| 10 | Correlations | **0.4778**, **0.5233**, **-0.692**; pairs `UNRESOLVED` |
| 11 | Independence and weights | No independence claim; weights unchanged |
| 12 | Composite weights | **30 / 25 / 20 / 15 / 10** for both composites |
| 13 | `mu_peer` | Format-specific, unweighted player mean; \(\ge1\) valid pressure opportunity; no gates; no cross-format pooling |
| 14 | Kish caveat | \(N_{eff}\) overstates independent information; thresholds retained |
| 15 | Edge cases | Invalid `balls_rem`, zero-ball, unresolved target, Super Over, interrupted |
| 16 | Reliability parameters | **\(\gamma=0.80\)**; replacement **50** at \(Z^*_{std}=0\); format gates **75 / 35**; final eligibility \(F\) non-empty AND \(M_{role}\ge10\) |
| 17 | Sensitivity plan | \(P\) 55/60/65; \(K\) 25/50/100; \(N_{raw}\) 50/75/100; \(\rho>0.92\) |

### A.2 Additional approvals

| Decision | Final treatment |
| :--- | :--- |
| Match 48610 | `UNRESOLVED_TARGET`; **93** second-innings rows excluded from primary pressure and baseline; **101** first-innings rows retained; `MATCH_48610_P1_FALLBACK` sensitivity only; scoring corpus **191,963 / 812** |
| Role architecture | Two independent rankings; **one row per player per role**; all-rounders qualify independently; no combined all-rounder ranking in the primary |
| Wicket-rate \(N_{eff}\) | **A** primary: legal-delivery-only \(N_{eff}\); wide stumpings retained; legal-ball denominator |
| Wide stumpings | **25** total; **6** bowler-pressure; **19** outside; Ashwin and Nawaz eligible; max eligible \(\Delta Z_{comp}=0.000165\) (audit counts) |
| `other` boundary treatments | All-extras rule, provisional primary: **9,816** scoring / **9,827** audit; verified core **9,790** / **9,801**; legal only **9,756** / **9,767** |
| `other` count | **260 = 256 + 3 + 1**; zero `other` rows in the Match 48610 chase; classification `UNRESOLVED` |
| Dot ball | `team_runs == 0 AND is_legal_delivery`; audit corpus **64,785** legal dots; **10,105** legal zero-run wicket deliveries; **9,779** bowler-credited |
| \(\Delta \%Dot\) baseline | **120 legal balls**; approved dual gate (Q4); not empirically optimized |
| Match breadth / final eligibility | **\(F_{j,r}\) non-empty AND \(M_{role,j,r}\ge10\)**; \(M_{role}\) only from formats in \(F_{j,r}\); \(M_{all}\) and per-format \(M\ge10\) sensitivity only |
| \(N_{eff}\) roles | Metric-specific for shrinkage; delivery-level for eligibility |
| Calibration | Per role; one row per player per role; equal-weight format average; dual-format once; one-format once; \(M\ge10\) not applied; **n = 122 batter / 173 bowler** |
| Reliability calibration | \(Z^{*}_{std}=(Z^{*}_{comp}-\mu_{Zcomp})/\sigma_{Zcomp}\); Reliability \(=100/(1+\exp(-0.80Z^{*}_{std}))\); batter **0.1036068081 / 0.6610638828**; bowler **0.0256919707 / 0.6655792246** |
| Ranking order | \(Z^{*}_{comp}\) descending; higher \(\sum N_{eff,del}\); higher \(M_{role}\); higher \(\sum N_{raw}\); ascending `player_id` |
| Batter dismissal rate | **A** primary; **B** sensitivity |
| Batter boundary | Source `is_four`/`is_six` primary; runs proxy sensitivity |
| Cross-format entry | One player-level row **per role**; equal weighting primary; \(N_{eff}\) sensitivity required; capped \(N_{eff}\) optional, with \(C\) only if performed; no combined all-rounder primary |
| Season pooling | Equal per delivery primary; season-equal and 2024–2026-only sensitivities |
| `bowler_runs` | Derived as batter runs + extras for wide/overstep/`other`; otherwise batter runs |
| Sign convention | Positive performance and Z mean better; pressure scores separate |
| Phase RPO | Informational only; not used in equations |
| Phase boundaries | Proportional; 120-ball Death = balls 96–119 / overs 17–20 |
| Zero-ball deliveries | `INVALID`; exclude; never clamp |
| Rankings | None generated |

### A.3 Stage 4.1 approval questions (Q1–Q11)

All **11 approval questions** were approved as recommended and are applied in this Stage 4.2 document.

| # | Decision | Applied treatment |
| ---: | :--- | :--- |
| **Q1** | Role architecture | Two independent rankings — batter and bowler — one row per player per role. All-rounders qualify independently in both. No combined all-rounder ranking in the primary. |
| **Q2** | Match breadth and final eligibility | \(F_{j,r}\) remains the format set passing \(N_{raw}\), \(N_{eff,del}\), baseline, positive denominators, and finite \(Z_{comp}\). \(M_{role}\) is counted across formats in \(F_{j,r}\). Final eligibility = **\(F_{j,r}\) non-empty AND \(M_{role,j,r}\ge10\)**. \(M_{role}<10\) is excluded from final ranking; calibration is exempt. |
| **Q3** | Bowler baseline | **120 legal balls bowled**; legal-ball denominator; \(Econ_{base}=6\sum bowler\_runs/\sum legal\); \(Dot\%_{base}\) and \(BoundaryConcededRate_{base}\) on the same denominator; no peer fallback. |
| **Q4** | Batter baseline | Dual gate: **120 balls faced** for \(SR_{base}\) and \(DR_{base}\); **120 legal balls** for \(Dot\%_{base}\); both required. |
| **Q5** | \(F_{j,r}\), zero denominators, flags | \(F_{j,r}\) requires \(N_{raw}\ge75\), \(N_{eff,del}\ge35\), baseline sufficiency, all five denominators \(>0\), finite \(Z_{comp}\). Zero denominator \(\Rightarrow\) `INSUFFICIENT_SAMPLE`. Precedence: `INVALID` > `BASELINE_INSUFFICIENT` > `INSUFFICIENT_SAMPLE` > `M_BREADTH_INSUFFICIENT` > `RANKING_ELIGIBLE`. |
| **Q6** | \(\mu_{peer}\) and reference moments | \(\mu_{peer}\) = unweighted player mean, \(\ge1\) valid pressure opportunity, no gates, no cross-format pooling. Reference moments on the shrunk scale with population SD; \(M\ge10\) not applied. |
| **Q7** | Calibration and reliability | Per role, one row per player per role, equal-weight format average, \(M\ge10\) not applied, population SD. Calibrated reliability approved: \(Z^{*}_{std}=(Z^{*}_{comp}-\mu_{Zcomp})/\sigma_{Zcomp}\); Reliability \(=100/(1+\exp(-0.80Z^{*}_{std}))\). n = 122 batter / 173 bowler. |
| **Q8** | Ranking order and tie-break | Descending \(Z^{*}_{comp}\); higher \(\sum N_{eff,del}\) over \(F_{j,r}\); higher \(M_{role}\); higher \(\sum N_{raw}\); ascending `player_id`. Only ranking-eligible players are sorted. |
| **Q9** | Match 48610 | Exclude the **93** second-innings rows from pressure and personal baselines; retain the **101** first-innings rows. `MATCH_48610_P1_FALLBACK` is sensitivity only. Scoring corpus: **191,963 / 812**. |
| **Q10** | `other` extras | `PROVISIONAL_OTHER` primary uses the all-extras rule: scoring **9,816** / audit **9,827**. Mandatory sensitivities: verified core **9,790** / **9,801**; legal only **9,756** / **9,767**; plus `other`-as-legal economy/dot sensitivity. No result is fully verified. |
| **Q11** | Ranking universe and season weighting | Primary universe = all eligible players in the 812-match scoring corpus; RR/auction shortlist separate. Equal per-delivery season pooling; season-equal and 2024–2026-only sensitivities. |

### A.4 Final approval status

All items in A.1, A.2, and A.3 are approved and in force. The items still unresolved are the `other` classification, the correlation pair identities, and the Match 48610 DLS provenance (treatment resolved by exclusion; \(P_1\) fallback sensitivity only). Capped \(N_{eff}\)-proportional weighting is optional; \(C\) is not a primary implementation blocker and must be registered only if that optional analysis is later performed. The bowler baseline exposure rule is now approved (120 legal balls). These are explicitly flagged as limitations, not silently resolved.

---

**STAGE 4.2 METHODOLOGY COMPLETE AND APPROVED.**

*This document is the final Stage 4.2 methodology reference. Q1–Q11 are applied. The scoring corpus is 191,963 deliveries across 812 matches. Stage 5 primary scoring was implemented separately; see `reports/stage5_scoring_validation.md`. The methodology and all approved thresholds are unchanged.*
