# Stage 3 Independent Validation & Audit Report
**Project:** SupeRR Selector Season 2 — Identify the Most Reliable Players Under Pressure  
**Target Franchise:** Rajasthan Royals (IPL 2027 Auction & Retention Strategy)  
**Author:** Senior Cricket Analytics Researcher & Data Scientist  
**Date:** November 2026  
**Document Version:** 2.0 (Target Provenance Reclassification & Verification)

---

## 1. Confirmed Findings

### A. Pre-Delivery Feature Physics & Zero Data Leakage
- Continuous step transition equality confirmed:
  $$\text{runs\_before}_{i+1} = \text{runs\_before}_i + \text{team\_runs}_i$$
  $$\text{wickets\_before}_{i+1} = \text{wickets\_before}_i + \mathbb{I}(\text{is\_wicket}_i)$$
  $$\text{legal\_balls\_before}_{i+1} = \text{legal\_balls\_before}_i + \mathbb{I}(\text{is\_legal\_delivery}_i)$$
- At delivery 1 of every innings across all 812 completed matches: $\text{runs\_before}_1 = 0$, $\text{wickets\_before}_1 = 0$, $\text{legal\_balls\_before}_1 = 0$.
- Deliveries are strictly chronologically ordered by `['match_id', 'innings', 'innings_ball_num', 'overid', 'over_ball_num']` with zero duplicate keys.
- `balls_remaining` is strictly $\ge 1.0$ for every delivery in the dataset, completely eliminating any potential division by zero.

### B. Audit of Legal-Ball Counting Around Extras
- The mathematical logic for calculating pre-delivery legal balls was traced directly in `src/feature_engineering.py`:
  $$\text{legal\_balls\_before}_i = \text{cumsum}(\text{is\_legal\_delivery}) - \text{is\_legal\_delivery}_i$$
- **Rule Verification**:
  1. A wide has $\text{is\_legal\_delivery}_i = \text{False}$. Its contribution to the cumulative sum is $0$. Therefore, the value of $\text{legal\_balls\_before}_{i+1}$ on the subsequent delivery is identical to $\text{legal\_balls\_before}_i$.
  2. A no-ball (`Overstep` or `other`) has $\text{is\_legal\_delivery}_i = \text{False}$. It likewise leaves $\text{legal\_balls\_before}_{i+1}$ unchanged.
  3. Consecutive wides or no-balls in the same over leave $\text{legal\_balls\_before}$ unchanged across all occurrences.
  4. A legal delivery has $\text{is\_legal\_delivery}_i = \text{True}$. It increments the cumulative sum by $1$, advancing $\text{legal\_balls\_before}_{i+1}$ by exactly $1$.
  5. The apparent discrepancy in the earlier Stage 3 report narrative was due to a prose caption error that misidentified ball 20.2 as the wide instead of ball 20.1 in Match 13512, whereas the underlying data and code were computing the correct legal ball sequence.

---

## 2. Target Provenance Reclassification (All 23 Matches with `revised_target`)

To prevent mislabeling ordinary targets as DLS revisions, target provenance is stratified into four rigorous categories:
- **`STANDARD_TARGET`**: Ordinary first-innings total + 1. Applied when no revised target exists, or when `revised_target == first_innings_total + 1` (where both teams played equal curtailed overs without resource asymmetry).
- **`VERIFIED_REVISED_TARGET`**: A genuine revised target differing from `first_innings_total + 1`, whose meaning as the target-to-win is supported by match data and decisive conclusion.
- **`UNRESOLVED_TARGET`**: Target semantics cannot be established reliably (Match 48610 retrospective par, interrupted matches). Chase pressure features remain unavailable (`NaN`).
- **`NOT_APPLICABLE`**: First-innings / non-chase deliveries.

### Detailed Audit Table of All 23 Matches:

| Match ID | Date | Competition | Teams | 1st Inn Total | Ordinary Target (Inn1 + 1) | Raw `revised_target` | Pipeline Target Used | Target Provenance | Supporting Classification Rationale |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `13612` | 2022-02-11 | SL in AUS T20I | AUS vs SL | 149 | 150 | 143.0 | 143.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 19 ov (114b). DLS target reduced from 150 to 143. Match ended at 114 balls; SL scored 122/8, AUS won by 20 runs. |
| `16754` | 2022-08-17 | AFG in IRE T20I | IRE vs AFG | 95 | 96 | 56.0 | 56.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 7 ov (42b). DLS target reduced from 96 to 56. IRE scored 56/3 in 40 balls; match ended immediately on target crossing. |
| `17395` | 2022-09-23 | AUS in IND T20I | IND vs AUS | 90 | 91 | 91.0 | 91.0 | `STANDARD_TARGET` | Both innings had identical revised overs (8 ov = 48b). `revised_target` equals ordinary target (90 + 1 = 91). No DLS adjustment applied. |
| `17765` | 2022-10-14 | ENG in AUS T20I | AUS vs ENG | 112 | 113 | 130.0 | NaN | `UNRESOLVED_TARGET` | Match interrupted by rain and abandoned without result (No Result after 23 balls). Chase incomplete; target unused. |
| `21586` | 2023-05-29 | IPL 2023 Final | CSK vs GT | 214 | 215 | 171.0 | 171.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 15 ov (90b). DLS target set at 171. CSK scored 171/5 on final ball; match concluded immediately. |
| `21070` | 2023-03-27 | IRE in BAN T20I | BAN vs IRE | 207 | 208 | 104.0 | 104.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 8 ov (48b). DLS target set at 104. IRE scored 81/5 in 48 balls; BAN won by 22 runs. |
| `21071` | 2023-03-29 | IRE in BAN T20I | BAN vs IRE | 202 | 203 | 203.0 | 203.0 | `STANDARD_TARGET` | Both innings had identical revised overs (17 ov = 102b). `revised_target` equals ordinary target (202 + 1 = 203). No DLS adjustment applied. |
| `28046` | 2023-12-12 | IND in SA T20I | SA vs IND | 180 | 181 | 152.0 | 152.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 15 ov (90b). DLS target set at 152. SA reached 154/5 in 83 balls; match concluded immediately upon target crossing. |
| `29984` | 2024-02-25 | AUS in NZ T20I | NZ vs AUS | 118 | 119 | 126.0 | 126.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 10 ov (60b). DLS target increased to 126. NZ scored 98/3 in 60 balls; AUS won by 27 runs. |
| `37354` | 2024-11-14 | PAK in AUS T20I | AUS vs PAK | 93 | 94 | 94.0 | 94.0 | `STANDARD_TARGET` | Both innings had identical revised overs (7 ov = 42b). `revised_target` equals ordinary target (93 + 1 = 94). No DLS adjustment applied. |
| `36098` | 2024-08-28 | SA in WI T20I | WI vs SA | 108 | 109 | 116.0 | 116.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 13 ov (78b). DLS target increased to 116. WI reached 116/2 in 56 balls; match concluded immediately upon target crossing. |
| `34428` | 2024-07-28 | IND in SL T20I | SL vs IND | 161 | 162 | 78.0 | 78.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 8 ov (48b). DLS target set at 78. IND reached 81/3 in 39 balls; match concluded immediately upon target crossing. |
| `36208` | 2025-09-10 | SA in ENG T20I | ENG vs SA | 97 | 98 | 69.0 | 69.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 5 ov (30b). DLS target set at 69. ENG scored 54/5 in 30 balls; SA won by 14 runs. |
| `40727` | 2025-04-18 | IPL 2025 | RCB vs PBKS | 95 | 96 | 96.0 | 96.0 | `STANDARD_TARGET` | Both innings had identical revised overs (14 ov = 84b). `revised_target` equals ordinary target (95 + 1 = 96). No DLS adjustment applied. |
| `40749` | 2025-05-06 | IPL 2025 | MI vs GT | 155 | 156 | 147.0 | 147.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 19 ov (114b). DLS target set at 147. GT reached 147/7 on ball 114; match concluded immediately. |
| `39809` | 2025-03-18 | PAK in NZ T20I | NZ vs PAK | 135 | 136 | 136.0 | 136.0 | `STANDARD_TARGET` | Both innings had identical revised overs (15 ov = 90b). `revised_target` equals ordinary target (135 + 1 = 136). No DLS adjustment applied. |
| `41851` | 2026-02-01 | WI in SA T20I | SA vs WI | 114 | 115 | 125.0 | 125.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 10 ov (60b). DLS target increased to 125. SA scored 118/6 in 60 balls; WI won by 6 runs. |
| `50137` | 2026-04-07 | IPL 2026 | RR vs MI | 150 | 151 | 151.0 | 151.0 | `STANDARD_TARGET` | Both innings had identical revised overs (11 ov = 66b). `revised_target` equals ordinary target (150 + 1 = 151). No DLS adjustment applied. |
| `50371` | 2026-05-07 | IPL 2026 | LSG vs RCB | 209 | 210 | 213.0 | 213.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 19 ov (114b). DLS target set at 213. RCB scored 203/6 in 114 balls; LSG won by 9 runs. |
| `48610` | 2026-01-30 | ENG in SL T20I | SL vs ENG | 133 | 134 | 115.0 | **NaN** | **`UNRESOLVED_TARGET`** | Retrospective par cutoff (115.0) at rain stoppage after 15 ov; team batted through over 15.0 to 125/4. Chase features left unavailable (`NaN`) to prevent zero-pressure artifacts. |
| `48611` | 2026-02-01 | ENG in SL T20I | SL vs ENG | 189 | 190 | 168.0 | 168.0 | `VERIFIED_REVISED_TARGET` | Innings 2 curtailed to 17 ov (102b). DLS target set at 168. ENG reached 173/4 in 100 balls; match concluded immediately upon target crossing. |
| `50190` | 2026-05-02 | NZ in BAN T20I | BAN vs NZ | 102 | 103 | 103.0 | 103.0 | `STANDARD_TARGET` | Both innings had identical revised overs (15 ov = 90b). `revised_target` equals ordinary target (102 + 1 = 103). No DLS adjustment applied. |
| `54711` | 2026-09-22 | IND in JPN T20I | JPN vs IND | 32 | 33 | 33.0 | 33.0 | `STANDARD_TARGET` | Both innings had identical revised overs (5 ov = 30b). `revised_target` equals ordinary target (32 + 1 = 33). No DLS adjustment applied. |

---

## 3. Summary of Provenance Stratification Across Primary Dataset

In the primary completed dataset (`data/processed/delivery_pressure_features.csv`, 192,056 deliveries):

| Target Provenance Category | Delivery Count | Match Count | Analytical Treatment |
| :--- | :---: | :---: | :--- |
| **`NOT_APPLICABLE`** | **100,210** | 812 | Innings 1 setting phase. Target features are `NaN`. |
| **`STANDARD_TARGET`** | **90,757** | **798** | Ordinary chase targets ($\text{first\_innings\_total} + 1$). Includes 790 standard fixtures without revised targets + 8 equal-overs curtailed matches. |
| **`VERIFIED_REVISED_TARGET`** | **996** | **13** | Genuine DLS revisions resulting from unequal resource allocation; match ended cleanly on target completion. |
| **`UNRESOLVED_TARGET`** | **93** | **1** (Match 48610) | Live chase target is unrecorded; chase features (`target_score`, `runs_required`, `required_run_rate`) remain unavailable (`NaN`). |
| **Total Completed Deliveries / Matches** | **192,056** | **812** | **100% Reconciled ($798 + 13 + 1 = 812$); Zero Deliveries / Matches Unaccounted For** |

---

## 4. Tests Performed and Actual Results

The automated test suite `tests/test_feature_engineering.py` was updated with 10 comprehensive test cases:

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

Combined with Stage 2 (`test_data_cleaning.py`), **19 automated tests** are executing cleanly in 1.46s across the test suite:
```text
Ran 19 tests in 1.460s
OK (All 19 tests passed)
```

---

**STAGE 3 FINAL DLS TARGET CLASSIFICATION CORRECTION IS COMPLETE.**
