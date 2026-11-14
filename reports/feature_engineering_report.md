# Delivery-Level Feature Engineering Report
**Project:** SupeRR Selector Season 2 — Identify the Most Reliable Players Under Pressure  
**Target Franchise:** Rajasthan Royals (IPL 2027 Auction & Retention Strategy)  
**Author:** Senior Cricket Analytics Researcher & Data Scientist  
**Date:** November 2026  
**Pipeline Version:** 3.2 (Target Provenance Stratification & Zero Leakage)

---

## 1. Executive Summary

This report documents the design, mathematical formulation, and validation of delivery-level features engineered for the SupeRR Selector Season 2 pressure engine. 

### Core Architectural Principles
1. **Strict Pre-Delivery State (Zero Information Leakage)**: Every situational feature reflects the exact match state immediately *before* the bowler releases the ball. Outcomes of the current ball (runs scored, wickets taken, extras conceded) are completely excluded from the pre-ball state.
2. **Innings Asymmetry**: First-innings target-setting dynamics and second-innings chase mechanics are modeled separately with dedicated feature spaces.
3. **Match-Specific Over Limits**: Revised over limits from rain-curtailed matches (`first_inn_revised_overs` and `second_inn_revised_overs` in 6-ball units) are integrated dynamically rather than assuming a static 120-ball allocation.
4. **Target Provenance Stratification**: 
   - `STANDARD_TARGET`: Ordinary $\text{first\_innings\_total} + 1$. Includes standard 20-over fixtures and the 8 equal-overs curtailed matches where `revised_target == first_innings_total + 1`.
   - `VERIFIED_REVISED_TARGET`: 13 matches with genuine DLS resource asymmetry whose meaning as the target-to-win is validated by match conclusion.
   - `UNRESOLVED_TARGET`: Match 48610 (retrospective par cutoff) and interrupted matches. Chase target features remain unavailable (`NaN`) to prevent zero-pressure artifacts.
   - `NOT_APPLICABLE`: Innings 1 setting phase.
5. **Zero Synthetic Post-Target Deliveries**: Because Match 48610's live target is left unresolved, exactly zero deliveries in the primary dataset carry false post-victory flags.
6. **Cohort Segmentation**: The primary completed-match dataset (192,056 deliveries) is isolated from interrupted matches (1,932 deliveries) and Super Overs (26 deliveries).

---

## 2. Dataset Segregation and Inventory

The 194,014 deliveries from the Stage 2 cleaned scope are partitioned into three distinct analytical datasets:

| Dataset Name | Output Path | Match Cohort | Delivery Count | Match Count | Primary Use Case |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Primary Pressure Corpus** | `data/processed/delivery_pressure_features.csv` | `COMPLETED` | **192,056** | **812** | Core modeling dataset for pressure scoring, batter reliability, and bowler reliability. |
| **Interrupted Corpus** | `data/processed/interrupted_delivery_features.csv` | `INTERRUPTED_NO_RESULT` | **1,932** | **25** | Preserved auxiliary set for partial-match context; isolated from competitive rankings. |
| **Super Over Corpus** | `data/processed/super_over_delivery_features.csv` | Super Overs | **26** | **4** | High-leverage single-over tiebreaker dataset evaluated independently. |
| **Total Scope Accounted For** | — | — | **194,014** | **853** | **100% Data Preservation** |

---

## 3. Mathematical Definitions of Pre-Delivery Features

For any delivery $i$ belonging to an innings:

### A. General Match Situation Features (Applicable to Innings 1 & 2)

1. **Runs Before Delivery (`runs_before`)**:
   $$\text{runs\_before}_i = \sum_{j < i} \text{team\_runs}_j = \text{cumsum}(\text{team\_runs}) - \text{team\_runs}_i$$
   *Range*: $0$ to $287$ runs. Value at ball 1 is always $0$.

2. **Wickets Lost Before Delivery (`wickets_before`)**:
   $$\text{wickets\_before}_i = \sum_{j < i} \text{is\_wicket}_j = \text{cumsum}(\text{is\_wicket}) - \text{is\_wicket}_i$$
   *Range*: $0$ to $9$ wickets. Excludes the current delivery's dismissal.

3. **Wickets in Hand (`wickets_remaining`)**:
   $$\text{wickets\_remaining}_i = 10 - \text{wickets\_before}_i$$
   *Range*: $1$ to $10$ wickets. Strictly $\ge 1$ across all active deliveries.

4. **Legal Deliveries Bowled (`legal_balls_before`)**:
   $$\text{legal\_balls\_before}_i = \sum_{j < i} \text{is\_legal\_delivery}_j = \text{cumsum}(\text{is\_legal\_delivery}) - \text{is\_legal\_delivery}_i$$
   *Note*: Wides, oversteps, and other no-balls do not increment this counter.

5. **Maximum Scheduled Balls (`max_balls`)**:
   Match-specific allocation derived from `cleaned_matches.csv`:
   - Innings 1: $\text{first\_inn\_revised\_overs}$ if valid, else $120.0$.
   - Innings 2: $\text{second\_inn\_revised\_overs}$ if valid, elif $\text{first\_inn\_revised\_overs}$ valid, else $120.0$.
   - Super Overs: $6.0$.

6. **Balls Remaining in Innings (`balls_remaining`)**:
   $$\text{balls\_remaining}_i = \max(0.0, \text{max\_balls}_i - \text{legal\_balls\_before}_i)$$
   *Property*: Strictly $\ge 1.0$ for all recorded deliveries (no division by zero in downstream rates).

7. **Innings Progression Ratio (`innings_progress`)**:
   $$\text{innings\_progress}_i = \min\left(1.0, \frac{\text{legal\_balls\_before}_i}{\text{max\_balls}_i}\right)$$
   *Range*: $[0.0, 1.0)$. Measures the chronological maturity of the innings.

8. **Current Run Rate (`current_run_rate`)**:
   $$\text{current\_run\_rate}_i = \begin{cases} 0.0 & \text{if } \text{legal\_balls\_before}_i = 0 \\ \frac{\text{runs\_before}_i \times 6.0}{\text{legal\_balls\_before}_i} & \text{if } \text{legal\_balls\_before}_i > 0 \end{cases}$$
   *Property*: Non-negative; tracks live scoring velocity.

9. **Tactical Innings Phase (`phase`)**:
   Categorized dynamically based on $\text{max\_balls}$:
   - `POWERPLAY`: $\text{legal\_balls\_before} < 0.30 \times \text{max\_balls}$ (balls $0$ to $35$ in 20-over game)
   - `MIDDLE`: $0.30 \times \text{max\_balls} \le \text{legal\_balls\_before} < 0.80 \times \text{max\_balls}$ (balls $36$ to $95$)
   - `DEATH`: $\text{legal\_balls\_before} \ge 0.80 \times \text{max\_balls}$ (balls $96$ to $119$)

---

### B. Chase-Specific Features (Innings 2 Only)

1. **Target Provenance (`target_provenance`)**:
   - `STANDARD_TARGET`: 90,757 deliveries across 797 matches (789 standard fixtures + 8 equal-overs curtailed matches).
   - `VERIFIED_REVISED_TARGET`: 996 deliveries across 13 matches with genuine DLS resource adjustments.
   - `UNRESOLVED_TARGET`: 93 deliveries (Match 48610). Chase pressure features remain unavailable (`NaN`).
   - `NOT_APPLICABLE`: 100,210 deliveries in Innings 1.

2. **Target Score (`target_score`)**:
   - Populated for verified targets; `NaN` for Innings 1 and unresolved targets.

3. **Runs Required (`runs_required`)**:
   $$\text{runs\_required}_i = \max(0.0, \text{target\_score} - \text{runs\_before}_i)$$
   Clamped at $0.0$; non-negative for 100% of verified chase deliveries.

4. **Required Run Rate (`required_run_rate`)**:
   $$\text{required\_run\_rate}_i = \frac{\text{runs\_required}_i \times 6.0}{\text{balls\_remaining}_i}$$
   Non-negative and free of `NaN` or `Inf` across verified chase deliveries.

5. **Required vs. Current Rate Strain (`rrr_minus_crr`)**:
   $$\text{rrr\_minus\_crr}_i = \text{required\_run\_rate}_i - \text{current\_run\_rate}_i$$

---

## 4. Empirical 20-Ball Sequence Validation (Match 14098, Innings 2)

The table below demonstrates 20 consecutive deliveries from Match 14098 (SRH vs Rajasthan Royals, IPL 2022) illustrating pre-delivery updates around wides, no-balls, wickets, and boundaries:

| Over | Ball | InnBall | Striker | Bowler | Runs | Extras | Extra Type | Legal? | Wkt? | Runs Before | Wkts Before | Legal Before | Balls Rem | CRR | Target | Req Runs | RRR |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 18 | 2 | 106 | W Sundar | P Krishna | 1 | 0 | none | True | False | 106 | 6 | 103 | 17.0 | 6.17 | 211.0 | 105.0 | 37.06 |
| 18 | 3 | 107 | A Markram | P Krishna | 1 | 0 | none | True | False | 107 | 6 | 104 | 16.0 | 6.17 | 211.0 | 104.0 | 39.00 |
| 18 | 4 | 108 | W Sundar | P Krishna | 1 | 0 | none | True | False | 108 | 6 | 105 | 15.0 | 6.17 | 211.0 | 103.0 | 41.20 |
| 18 | 5 | 109 | A Markram | P Krishna | 6 | 0 | none | True | False | 109 | 6 | 106 | 14.0 | 6.17 | 211.0 | 102.0 | 43.71 |
| 18 | 6 | 110 | A Markram | P Krishna | 4 | 0 | none | True | False | 115 | 6 | 107 | 13.0 | 6.45 | 211.0 | 96.0 | 44.31 |
| 19 | 1 | 111 | W Sundar | T Boult | 1 | 0 | none | True | False | 119 | 6 | 108 | 12.0 | 6.61 | 211.0 | 92.0 | 46.00 |
| 19 | 2 | 112 | A Markram | T Boult | 1 | 0 | none | True | False | 120 | 6 | 109 | 11.0 | 6.61 | 211.0 | 91.0 | 49.64 |
| 19 | 3 | 113 | W Sundar | T Boult | 4 | 0 | none | True | False | 121 | 6 | 110 | 10.0 | 6.60 | 211.0 | 90.0 | 54.00 |
| 19 | 4 | 114 | W Sundar | T Boult | 0 | 1 | wide | False | False | 125 | 6 | 111 | 9.0 | 6.76 | 211.0 | 86.0 | 57.33 |
| 19 | 5 | 115 | W Sundar | T Boult | 6 | 0 | none | True | False | 126 | 6 | **111** | **9.0** | 6.81 | 211.0 | 85.0 | 56.67 |
| 19 | 6 | 116 | W Sundar | T Boult | 0 | 1 | wide | False | False | 132 | 6 | 112 | 8.0 | 7.07 | 211.0 | 79.0 | 59.25 |
| 19 | 7 | 117 | W Sundar | T Boult | 0 | 0 | none | True | **True** | 133 | **6** | **112** | **8.0** | 7.13 | 211.0 | 78.0 | 58.50 |
| 19 | 8 | 118 | B Kumar | T Boult | 1 | 0 | none | True | False | 133 | **7** | 113 | 7.0 | 7.06 | 211.0 | 78.0 | 66.86 |
| 20 | 1 | 119 | B Kumar | N Coulter-Nile| 0 | 1 | other | False | False | 134 | 7 | 114 | 6.0 | 7.05 | 211.0 | 77.0 | 77.00 |
| 20 | 2 | 120 | B Kumar | R Parag | 1 | 0 | none | True | False | 135 | 7 | **114** | **6.0** | 7.11 | 211.0 | 76.0 | 76.00 |
| 20 | 3 | 121 | A Markram | R Parag | 1 | 0 | none | True | False | 136 | 7 | 115 | 5.0 | 7.10 | 211.0 | 75.0 | 90.00 |
| 20 | 4 | 122 | B Kumar | R Parag | 1 | 0 | none | True | False | 137 | 7 | 116 | 4.0 | 7.09 | 211.0 | 74.0 | 111.00 |
| 20 | 5 | 123 | A Markram | R Parag | 4 | 0 | none | True | False | 138 | 7 | 117 | 3.0 | 7.08 | 211.0 | 73.0 | 146.00 |
| 20 | 6 | 124 | A Markram | R Parag | 6 | 0 | none | True | False | 142 | 7 | 118 | 2.0 | 7.22 | 211.0 | 69.0 | 207.00 |
| 20 | 7 | 125 | A Markram | R Parag | 1 | 0 | none | True | False | 148 | 7 | 119 | 1.0 | 7.46 | 211.0 | 63.0 | 378.00 |

---

## 5. Automated Validation Test Results (`tests/test_feature_engineering.py`)

```text
tests/test_feature_engineering.py:
  test_01_dataset_dimensions_and_preservation ............. PASSED
  test_02_zero_data_leakage ............................... PASSED
  test_03_wide_followed_immediately_by_legal_delivery ..... PASSED
  test_04_noball_followed_immediately_by_legal_delivery ... PASSED
  test_05_multiple_wides_in_same_over ..................... PASSED
  test_06_wicket_and_runs_pre_delivery_isolation .......... PASSED
  test_07_target_provenance_classification_integrity ...... PASSED
  test_08_unresolved_targets_not_used_for_chase_calc ...... PASSED
  test_09_raw_revised_target_values_preserved ............. PASSED
  test_10_target_provenance_and_score_consistency ......... PASSED

----------------------------------------------------------------------
Ran 10 tests in 0.927s

OK (100% Pass Rate)
```

**STAGE 3 DELIVERY-LEVEL FEATURE ENGINEERING IS AUDITED, RECONCILED, AND FULLY COMPLETE.**
