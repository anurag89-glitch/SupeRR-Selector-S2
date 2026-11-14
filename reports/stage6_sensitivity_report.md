# Stage 6 — Sensitivity Analysis and Ranking Robustness

**Project:** SupeRR Selector Season 2 — Identify the Most Reliable Players Under Pressure  
**Status:** COMPLETE  
**Reference ranking:** approved Stage 5 primary rankings, unchanged  
**Primary method:** equal format weighting, $P=60$, $K=50$, $N_{raw}\ge75$, $N_{eff}\ge35$, $M_{role}\ge10$

---

## 1. Executive summary

The Stage 6 programme executed **21 approved scenarios** (the primary baseline plus 20 approved alternatives) and **10 supplementary diagnostics** that the Stage 4.2 methodology does not approve. Two scenarios were deliberately not run: capped $N_{eff}$ weighting (no registered numeric $C$) and an alternative baseline-exposure threshold (no pre-registered rule).

**Grid robustness passes.** Across the six approved Section 13.1 grid alternatives ($P=55/65$, $K=25/100$, $N_{raw}=50/100$), the minimum Spearman rank correlation is **0.9357 for batters** and **0.9722 for bowlers**, both above the approved $\rho>0.92$ target. Top-10 **membership** changes by at most four members under these perturbations; individual rank movements can be substantially larger and are quantified in Sections 4–5.

**Most approved non-grid alternatives are also stable.** Of the 14 approved mandatory alternatives outside the grid, 12 pass the $\rho>0.92$ target for both roles. The exceptions are **season-equal weighting** and the **2024–2026-only restriction**, which are not formula perturbations but changes to the effective season population. Both reduce the common eligible population and materially change the ranking, especially for bowlers.

**Top-10 membership overlap varies across the primary grid.** Batter overlap ranges from 7/10 to 10/10; bowler overlap ranges from 6/10 to 10/10. Overlap is lowest under the season-equal and 2024–2026 scenarios: batters 8/10 and 3/10; bowlers 5/10 and 4/10.

**Conclusion:** the approved Stage 5 ranking order is robust to the approved parameter grid and to the main measurement-definition alternatives (`other`, dismissal definition, boundary source, $N_{eff}$ scope, cross-format weighting, CRR baseline, eligibility gate, Match 48610 fallback), although top-10 membership turnover is material for some alternatives. It is **not robust to season-equal weighting or to restricting the data to 2024–2026**. Those results reflect a genuinely different evidence base and must be reported as a material limitation, not treated as a failure of the primary ranking. No approved primary score, threshold or rank was changed.

### Primary top 10

**Batters**

| Rank | Player ID | Player | Z_comp | Reliability | M_role |
| --- | --- | --- | --- | --- | --- |
| 1 | 3374 | Mark Chapman | 1.548019 | 85.170 | 24 |
| 2 | 4369 | Shai Hope | 1.426453 | 83.214 | 13 |
| 3 | 6288 | Shubman Gill | 1.365596 | 82.160 | 14 |
| 4 | 37052 | Naman Dhir | 1.330431 | 81.528 | 15 |
| 5 | 2485 | Babar Azam | 1.314673 | 81.239 | 13 |
| 6 | 2930 | Rassie van der Dussen | 1.191270 | 78.856 | 10 |
| 7 | 1699 | Suryakumar Yadav | 1.149888 | 78.009 | 47 |
| 8 | 2921 | Fakhar Zaman | 1.132561 | 77.647 | 20 |
| 9 | 4246 | Nitish Rana | 1.128585 | 77.563 | 26 |
| 10 | 6651 | Towhid Hridoy | 0.988046 | 74.466 | 22 |

**Bowlers**

| Rank | Player ID | Player | Z_comp | Reliability | M_role |
| --- | --- | --- | --- | --- | --- |
| 1 | 4658 | Nasum Ahmed | 1.669466 | 87.823 | 11 |
| 2 | 4840 | Odean Smith | 1.437026 | 84.506 | 10 |
| 3 | 7364 | Haris Rauf | 1.299349 | 82.214 | 30 |
| 4 | 7690 | Saim Ayub | 1.282356 | 81.913 | 11 |
| 5 | 781 | Sunil Narine | 1.232167 | 81.002 | 30 |
| 6 | 7699 | Abbas Afridi | 1.171518 | 79.855 | 18 |
| 7 | 1596 | Moeen Ali | 1.122670 | 78.894 | 12 |
| 8 | 7503 | Ravi Bishnoi | 1.049481 | 77.392 | 47 |
| 9 | 6643 | Hasan Mahmud | 1.011666 | 76.586 | 10 |
| 10 | 8661 | Matheesha Pathirana | 1.000287 | 76.340 | 29 |

---

## 2. Sensitivity methods and parameters

### Locked primary method

| Parameter | Primary value |
| --- | --- |
| Pressure cutoff $P$ | 60 |
| Shrinkage constant $K$ | 50 |
| Raw pressure deliveries $N_{raw}$ | 75 |
| Effective pressure deliveries $N_{eff,del}$ | 35 |
| Final match-breadth gate | F non-empty AND $M_{role}\ge10$ |
| Batter dismissal rate | Definition A: all legitimate striker dismissals |
| Batter boundary percentage | Source `is_four` / `is_six` flags |
| `other` extras | Provisional no-ball-like primary |
| Bowler boundary-conceded | All-extras rule (9,816 pressure boundaries) |
| Cross-format weighting | Equal format weights |
| CRR baseline | All-innings pooled: T20 9.3201, T20I 8.5516 |
| Match 48610 chase | 93 rows excluded from primary scoring |
| Season pooling | Equal per delivery |
| Bowling Gaussian width $\sigma_S$ | 12 runs |
| Binary finish leverage | 3.00 |
| Wicket-remaining resource depth $h$ | $\sqrt{W_{rem}/10}$ |
| Calibration | Fixed approved per-role $\mu_{Zcomp}$ / $\sigma_{Zcomp}$ |

Every scenario varies only the stated parameter. **Reference moments, peer means and calibration constants are held fixed at the approved primary values**, with one exception: the dismissal Definition B and runs-proxy batter boundary sensitivities use the alternative reference moments that Stage 4.2 publishes for those metric definitions (Sections 8.5 and 8.7). Definition B changes only the pressure dismissal numerator; the personal baseline remains Definition A, matching the published Section 8.7 impact table. This keeps each metric on its approved standardized scale while isolating the stated parameter change; it is not a re-estimation of the Stage 5 methodology.

### Scenario register

| Scenario | Category | Status | Approved | Change from primary |
| --- | --- | --- | --- | --- |
| K_100 | approved_grid | COMPLETED | yes | shrinkage_k 50 -> 100; all other parameters primary. |
| K_25 | approved_grid | COMPLETED | yes | shrinkage_k 50 -> 25; all other parameters primary. |
| NRAW_100 | approved_grid | COMPLETED | yes | raw_gate 75 -> 100; all other parameters primary. |
| NRAW_50 | approved_grid | COMPLETED | yes | raw_gate 75 -> 50; all other parameters primary. |
| P_55 | approved_grid | COMPLETED | yes | pressure_cutoff 60 -> 55; all other parameters primary. |
| P_65 | approved_grid | COMPLETED | yes | pressure_cutoff 60 -> 65; all other parameters primary. |
| BOUNDARY_RUNS_PROXY | approved_mandatory | COMPLETED | yes | Batter boundary numerator flags -> batter_runs proxy; bowler boundary-conceded retains source flags. Uses the Section 8.5 runs-proxy reference moments. |
| CRR_FIRST_INNINGS | approved_mandatory | COMPLETED | yes | CRR T20 9.3201 -> 9.3749 and T20I 8.5516 -> 8.6673; wicket baseline unchanged. |
| DISMISSAL_RATE_WIDE_EXCLUDED | approved_mandatory | COMPLETED | yes | D removes striker dismissals on wide deliveries from the pressure numerator; balls-faced denominator unchanged and personal baseline held at Definition A. Uses the Section 8.7 Definition B reference moments. |
| ELIG_M_ALL | approved_mandatory | COMPLETED | yes | ranking gate M_role>=10 -> M_all>=10; F_non-empty unchanged. |
| ELIG_PER_FORMAT_M10 | approved_mandatory | COMPLETED | yes | format gate adds M_format>=10; final M_role>=10 gate unchanged. |
| FORMAT_WEIGHT_NEFF_PROPORTIONAL | approved_mandatory | COMPLETED | yes | player Z_comp = sum(N_eff_del_f * Z_f) / sum(N_eff_del_f); equal weighting remains primary. |
| MATCH_48610_P1_FALLBACK | approved_mandatory | COMPLETED | yes | Include 192,056 audit rows and evaluate unresolved chase with P1 equations; primary still excludes the 93 rows. |
| NEFF_SCOPE_ALL_DELIVERIES | approved_mandatory | COMPLETED | yes | N_eff_legal -> N_eff_del for all five bowler metrics; metric raw denominators unchanged. |
| OTHER_AS_LEGAL | approved_mandatory | COMPLETED | yes | other_as_legal True; 256 other deliveries become legal; runs and bowler charges unchanged. |
| OTHER_BOUNDARY_LEGAL_ONLY | approved_mandatory | COMPLETED | yes | boundary_legality all -> legal; excludes 26 other and 34 overstep boundaries at P_bowl>=60 (9,816 -> 9,756). |
| OTHER_BOUNDARY_LEGAL_OVERSTEP | approved_mandatory | COMPLETED | yes | boundary_legality all -> legal_overstep; excludes 26 other-delivery boundaries at P_bowl>=60 (9,816 -> 9,790). |
| SEASON_2024_2026 | approved_mandatory | COMPLETED | yes | season_from 2024; 2022, 2022/23, 2023 and 2023/24 deliveries excluded. |
| SEASON_EQUAL | approved_mandatory | COMPLETED | yes | pressure weights divided by format-season weight total; delivery-level pooling remains primary. |
| WKT_RATE_NEFF_ALL_DELIVERIES | approved_mandatory | COMPLETED | yes | WktRate_P shrinkage N_eff uses N_eff_del instead of N_eff_legal; metric denominator and wide stumpings unchanged. |
| PRIMARY | baseline | PRIMARY | yes | None. |
| BASELINE_EXPOSURE_ALT | blocked | BLOCKED_NOT_APPROVED | no | Not run. |
| OPTIONAL_NEFF_CAPPED | optional | OPTIONAL_NOT_RUN | no | Not run. |
| SUPP_H_LINEAR | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | h sqrt(W_rem/10) -> W_rem/10; not an approved Stage 4.2 parameterization. |
| SUPP_H_QUADRATIC | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | h sqrt(W_rem/10) -> (W_rem/10)^2; not an approved Stage 4.2 parameterization. |
| SUPP_LEVERAGE_0 | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | leverage 3.00 -> 0.00; trigger unchanged; not an approved Stage 4.2 parameterization. |
| SUPP_LEVERAGE_1_5 | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | leverage 3.00 -> 1.50; trigger unchanged; not an approved Stage 4.2 parameterization. |
| SUPP_LEVERAGE_5 | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | leverage 3.00 -> 5.00; trigger unchanged; not an approved Stage 4.2 parameterization. |
| SUPP_SIGMA_10 | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | sigma 12 -> 10; not an approved Stage 4.2 parameterization. |
| SUPP_SIGMA_15 | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | sigma 12 -> 15; not an approved Stage 4.2 parameterization. |
| SUPP_SIGMA_20 | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | sigma 12 -> 20; not an approved Stage 4.2 parameterization. |
| SUPP_SIGMA_8 | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | sigma 12 -> 8; not an approved Stage 4.2 parameterization. |
| SUPP_WIDE_STUMP_REMOVED | supplementary_non_approved | COMPLETED_SUPPLEMENTARY | no | 25 wide stumpings (6 in bowler pressure set) removed from WktRate_P numerator; not an approved Stage 4.2 parameterization. |

### Stability definitions

- **Top-10 overlap:** number of players present in both the primary and scenario top 10.
- **Jaccard:** overlap divided by the size of the union of the two top-10 sets.
- **Spearman / Kendall:** rank correlations on the **common eligible population**, i.e. players who are ranking-eligible in both the primary and the scenario. Correlations are not computed across different populations.
- **Mean / max |Δrank|:** absolute change in final rank for common eligible players. Because the eligible population can change, rank changes are descriptive and are always reported alongside eligibility counts.
- **Most stable / most sensitive:** players with at least 10 approved-scenario comparisons; primary-top-10 views restrict the pool to the primary top 10.
- **Membership turnover versus individual rank movement:** top-10 overlap measures how many top-10 members are retained; it does **not** measure positional stability. A player can remain in the top 10 while moving several places, and individual rank movements can be substantially larger than the membership turnover. The mean and maximum $|\Delta rank|$ columns quantify those individual movements separately.

---

## 3. Primary versus alternative comparisons

### Approved scenarios (both roles)

| Scenario | Batter eligible | Batter top-10 | Batter ρ | Bowler eligible | Bowler top-10 | Bowler ρ |
| --- | --- | --- | --- | --- | --- | --- |
| BOUNDARY_RUNS_PROXY | 101 | 10/10 | 1.0000 | 141 | 10/10 | 1.0000 |
| CRR_FIRST_INNINGS | 101 | 8/10 | 0.9913 | 142 | 6/10 | 0.9760 |
| DISMISSAL_RATE_WIDE_EXCLUDED | 101 | 10/10 | 0.9998 | 141 | 10/10 | 1.0000 |
| ELIG_M_ALL | 103 | 10/10 | 1.0000 | 146 | 10/10 | 1.0000 |
| ELIG_PER_FORMAT_M10 | 101 | 9/10 | 0.9916 | 139 | 9/10 | 0.9778 |
| FORMAT_WEIGHT_NEFF_PROPORTIONAL | 101 | 9/10 | 0.9871 | 141 | 9/10 | 0.9868 |
| K_100 | 101 | 9/10 | 0.9969 | 141 | 8/10 | 0.9972 |
| K_25 | 101 | 10/10 | 0.9987 | 141 | 10/10 | 0.9987 |
| MATCH_48610_P1_FALLBACK | 101 | 10/10 | 1.0000 | 141 | 10/10 | 0.9997 |
| NEFF_SCOPE_ALL_DELIVERIES | 101 | 10/10 | 1.0000 | 141 | 10/10 | 0.9999 |
| NRAW_100 | 96 | 9/10 | 0.9988 | 126 | 6/10 | 0.9739 |
| NRAW_50 | 104 | 10/10 | 0.9923 | 145 | 9/10 | 0.9880 |
| OTHER_AS_LEGAL | 101 | 9/10 | 0.9999 | 141 | 10/10 | 0.9997 |
| OTHER_BOUNDARY_LEGAL_ONLY | 101 | 10/10 | 1.0000 | 141 | 10/10 | 0.9999 |
| OTHER_BOUNDARY_LEGAL_OVERSTEP | 101 | 10/10 | 1.0000 | 141 | 10/10 | 1.0000 |
| PRIMARY | 101 | 10/10 | 1.0000 | 141 | 10/10 | 1.0000 |
| P_55 | 108 | 7/10 | 0.9444 | 146 | 8/10 | 0.9744 |
| P_65 | 93 | 7/10 | 0.9357 | 133 | 6/10 | 0.9722 |
| SEASON_2024_2026 | 52 | 3/10 | 0.7624 | 98 | 4/10 | 0.8124 |
| SEASON_EQUAL | 98 | 8/10 | 0.8916 | 131 | 5/10 | 0.8777 |
| WKT_RATE_NEFF_ALL_DELIVERIES | 101 | 10/10 | 1.0000 | 141 | 10/10 | 1.0000 |

### Supplementary diagnostics (not approved by Stage 4.2)

| Scenario | Batter eligible | Batter top-10 | Batter ρ | Bowler eligible | Bowler top-10 | Bowler ρ |
| --- | --- | --- | --- | --- | --- | --- |
| SUPP_H_LINEAR | 101 | 10/10 | 1.0000 | 137 | 6/10 | 0.9212 |
| SUPP_H_QUADRATIC | 101 | 10/10 | 1.0000 | 130 | 3/10 | 0.8519 |
| SUPP_LEVERAGE_0 | 101 | 10/10 | 1.0000 | 141 | 9/10 | 0.9988 |
| SUPP_LEVERAGE_1_5 | 101 | 10/10 | 1.0000 | 141 | 9/10 | 0.9999 |
| SUPP_LEVERAGE_5 | 101 | 10/10 | 1.0000 | 141 | 10/10 | 1.0000 |
| SUPP_SIGMA_10 | 101 | 10/10 | 1.0000 | 140 | 7/10 | 0.9754 |
| SUPP_SIGMA_15 | 101 | 10/10 | 1.0000 | 143 | 8/10 | 0.9783 |
| SUPP_SIGMA_20 | 101 | 10/10 | 1.0000 | 158 | 7/10 | 0.9423 |
| SUPP_SIGMA_8 | 101 | 10/10 | 1.0000 | 134 | 6/10 | 0.9432 |
| SUPP_WIDE_STUMP_REMOVED | 101 | 10/10 | 1.0000 | 141 | 10/10 | 1.0000 |

---

## 4. Batter ranking stability

### Approved scenarios

| Scenario | Status | Eligible | Top-10 overlap | Jaccard | Spearman | Kendall | Entrants | Leavers | Mean |Δrank| | Max |Δrank| |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRIMARY | PRIMARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| P_55 | COMPLETED | 108 | 7/10 | 0.538 | 0.9444 | 0.8052 | 3 | 3 | 8.07 | 40.0 |
| P_65 | COMPLETED | 93 | 7/10 | 0.538 | 0.9357 | 0.8023 | 3 | 3 | 7.25 | 43.0 |
| K_25 | COMPLETED | 101 | 10/10 | 1.000 | 0.9987 | 0.9774 | 0 | 0 | 0.97 | 5.0 |
| K_100 | COMPLETED | 101 | 9/10 | 0.818 | 0.9969 | 0.9608 | 1 | 1 | 1.58 | 8.0 |
| NRAW_50 | COMPLETED | 104 | 10/10 | 1.000 | 0.9923 | 0.9770 | 0 | 0 | 1.50 | 32.0 |
| NRAW_100 | COMPLETED | 96 | 9/10 | 0.818 | 0.9988 | 0.9930 | 1 | 1 | 1.05 | 12.0 |
| WKT_RATE_NEFF_ALL_DELIVERIES | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| DISMISSAL_RATE_WIDE_EXCLUDED | COMPLETED | 101 | 10/10 | 1.000 | 0.9998 | 0.9956 | 0 | 0 | 0.22 | 4.0 |
| BOUNDARY_RUNS_PROXY | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 0.9988 | 0 | 0 | 0.06 | 2.0 |
| OTHER_BOUNDARY_LEGAL_OVERSTEP | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| OTHER_BOUNDARY_LEGAL_ONLY | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| OTHER_AS_LEGAL | COMPLETED | 101 | 9/10 | 0.818 | 0.9999 | 0.9976 | 1 | 1 | 0.12 | 1.0 |
| FORMAT_WEIGHT_NEFF_PROPORTIONAL | COMPLETED | 101 | 9/10 | 0.818 | 0.9871 | 0.9450 | 1 | 1 | 2.22 | 29.0 |
| CRR_FIRST_INNINGS | COMPLETED | 101 | 8/10 | 0.667 | 0.9913 | 0.9329 | 2 | 2 | 2.77 | 16.0 |
| ELIG_M_ALL | COMPLETED | 103 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.73 | 2.0 |
| ELIG_PER_FORMAT_M10 | COMPLETED | 101 | 9/10 | 0.818 | 0.9916 | 0.9798 | 1 | 1 | 1.01 | 35.0 |
| NEFF_SCOPE_ALL_DELIVERIES | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| MATCH_48610_P1_FALLBACK | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 0.9996 | 0 | 0 | 0.02 | 1.0 |
| SEASON_EQUAL | COMPLETED | 98 | 8/10 | 0.667 | 0.8916 | 0.7766 | 2 | 2 | 7.82 | 57.0 |
| SEASON_2024_2026 | COMPLETED | 52 | 3/10 | 0.176 | 0.7624 | 0.6169 | 7 | 7 | 24.00 | 73.0 |

### Supplementary scenarios

| Scenario | Status | Eligible | Top-10 overlap | Jaccard | Spearman | Kendall | Entrants | Leavers | Mean |Δrank| | Max |Δrank| |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SUPP_SIGMA_8 | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| SUPP_SIGMA_10 | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| SUPP_SIGMA_15 | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| SUPP_SIGMA_20 | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| SUPP_H_LINEAR | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| SUPP_H_QUADRATIC | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| SUPP_LEVERAGE_0 | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| SUPP_LEVERAGE_1_5 | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| SUPP_LEVERAGE_5 | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| SUPP_WIDE_STUMP_REMOVED | COMPLETED_SUPPLEMENTARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |

### Most stable primary top-10 batters

| Player | Primary rank | Top-10 appearances | Mean |Δrank| | Max |Δrank| | Worst scenario | Mean |ΔZ| |
| --- | --- | --- | --- | --- | --- | --- |
| 3374 Mark Chapman | 1 | 19/19 | 0.47 | 4.0 | P_55 | 0.0664 |
| 2921 Fakhar Zaman | 8 | 20/20 | 0.50 | 4.0 | P_65 | 0.0426 |
| 37052 Naman Dhir | 4 | 20/20 | 0.55 | 3.0 | P_55 | 0.0516 |
| 6288 Shubman Gill | 3 | 19/19 | 0.63 | 7.0 | P_65 | 0.0734 |
| 2930 Rassie van der Dussen | 6 | 16/17 | 0.76 | 5.0 | CRR_FIRST_INNINGS | 0.0395 |
| 4369 Shai Hope | 2 | 19/19 | 0.79 | 5.0 | P_55 | 0.0910 |
| 6651 Towhid Hridoy | 10 | 13/20 | 1.05 | 7.0 | P_55 | 0.0545 |
| 2485 Babar Azam | 5 | 18/19 | 1.63 | 22.0 | SEASON_EQUAL | 0.1041 |

### Most sensitive primary top-10 batters

| Player | Primary rank | Top-10 appearances | Mean |Δrank| | Max |Δrank| | Worst scenario | Mean |ΔZ| |
| --- | --- | --- | --- | --- | --- | --- |
| 4246 Nitish Rana | 9 | 17/20 | 3.50 | 36.0 | P_65 | 0.1507 |
| 1699 Suryakumar Yadav | 7 | 17/20 | 2.30 | 29.0 | SEASON_2024_2026 | 0.1247 |
| 2485 Babar Azam | 5 | 18/19 | 1.63 | 22.0 | SEASON_EQUAL | 0.1041 |
| 6651 Towhid Hridoy | 10 | 13/20 | 1.05 | 7.0 | P_55 | 0.0545 |
| 4369 Shai Hope | 2 | 19/19 | 0.79 | 5.0 | P_55 | 0.0910 |
| 2930 Rassie van der Dussen | 6 | 16/17 | 0.76 | 5.0 | CRR_FIRST_INNINGS | 0.0395 |
| 6288 Shubman Gill | 3 | 19/19 | 0.63 | 7.0 | P_65 | 0.0734 |
| 37052 Naman Dhir | 4 | 20/20 | 0.55 | 3.0 | P_55 | 0.0516 |

### Largest batter rank movements across approved scenarios

| Player | Primary rank | Top-10 appearances | Mean |Δrank| | Max |Δrank| | Worst scenario | Mean |ΔZ| |
| --- | --- | --- | --- | --- | --- | --- |
| 4246 Nitish Rana | 9 | 17/20 | 3.50 | 36.0 | P_65 | 0.1507 |
| 1699 Suryakumar Yadav | 7 | 17/20 | 2.30 | 29.0 | SEASON_2024_2026 | 0.1247 |
| 2485 Babar Azam | 5 | 18/19 | 1.63 | 22.0 | SEASON_EQUAL | 0.1041 |
| 6288 Shubman Gill | 3 | 19/19 | 0.63 | 7.0 | P_65 | 0.0734 |
| 6651 Towhid Hridoy | 10 | 13/20 | 1.05 | 7.0 | P_55 | 0.0545 |
| 4369 Shai Hope | 2 | 19/19 | 0.79 | 5.0 | P_55 | 0.0910 |
| 2930 Rassie van der Dussen | 6 | 16/17 | 0.76 | 5.0 | CRR_FIRST_INNINGS | 0.0395 |
| 3374 Mark Chapman | 1 | 19/19 | 0.47 | 4.0 | P_55 | 0.0664 |
| 2921 Fakhar Zaman | 8 | 20/20 | 0.50 | 4.0 | P_65 | 0.0426 |
| 37052 Naman Dhir | 4 | 20/20 | 0.55 | 3.0 | P_55 | 0.0516 |

---

## 5. Bowler ranking stability

### Approved scenarios

| Scenario | Status | Eligible | Top-10 overlap | Jaccard | Spearman | Kendall | Entrants | Leavers | Mean |Δrank| | Max |Δrank| |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRIMARY | PRIMARY | 141 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| P_55 | COMPLETED | 146 | 8/10 | 0.667 | 0.9744 | 0.8843 | 2 | 2 | 6.67 | 54.0 |
| P_65 | COMPLETED | 133 | 6/10 | 0.429 | 0.9722 | 0.8693 | 4 | 4 | 7.85 | 59.0 |
| K_25 | COMPLETED | 141 | 10/10 | 1.000 | 0.9987 | 0.9757 | 0 | 0 | 1.50 | 7.0 |
| K_100 | COMPLETED | 141 | 8/10 | 0.667 | 0.9972 | 0.9572 | 2 | 2 | 2.41 | 8.0 |
| NRAW_50 | COMPLETED | 145 | 9/10 | 0.818 | 0.9880 | 0.9550 | 1 | 1 | 2.57 | 38.0 |
| NRAW_100 | COMPLETED | 126 | 6/10 | 0.429 | 0.9739 | 0.9451 | 4 | 4 | 8.97 | 61.0 |
| WKT_RATE_NEFF_ALL_DELIVERIES | COMPLETED | 141 | 10/10 | 1.000 | 1.0000 | 0.9982 | 0 | 0 | 0.13 | 2.0 |
| DISMISSAL_RATE_WIDE_EXCLUDED | COMPLETED | 141 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| BOUNDARY_RUNS_PROXY | COMPLETED | 141 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| OTHER_BOUNDARY_LEGAL_OVERSTEP | COMPLETED | 141 | 10/10 | 1.000 | 1.0000 | 0.9986 | 0 | 0 | 0.10 | 2.0 |
| OTHER_BOUNDARY_LEGAL_ONLY | COMPLETED | 141 | 10/10 | 1.000 | 0.9999 | 0.9976 | 0 | 0 | 0.17 | 2.0 |
| OTHER_AS_LEGAL | COMPLETED | 141 | 10/10 | 1.000 | 0.9997 | 0.9913 | 0 | 0 | 0.58 | 3.0 |
| FORMAT_WEIGHT_NEFF_PROPORTIONAL | COMPLETED | 141 | 9/10 | 0.818 | 0.9868 | 0.9449 | 1 | 1 | 2.95 | 45.0 |
| CRR_FIRST_INNINGS | COMPLETED | 142 | 6/10 | 0.429 | 0.9760 | 0.8808 | 4 | 4 | 6.04 | 56.0 |
| ELIG_M_ALL | COMPLETED | 146 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 2.42 | 5.0 |
| ELIG_PER_FORMAT_M10 | COMPLETED | 139 | 9/10 | 0.818 | 0.9778 | 0.9566 | 1 | 1 | 2.71 | 67.0 |
| NEFF_SCOPE_ALL_DELIVERIES | COMPLETED | 141 | 10/10 | 1.000 | 0.9999 | 0.9959 | 0 | 0 | 0.27 | 2.0 |
| MATCH_48610_P1_FALLBACK | COMPLETED | 141 | 10/10 | 1.000 | 0.9997 | 0.9968 | 0 | 0 | 0.23 | 10.0 |
| SEASON_EQUAL | COMPLETED | 131 | 5/10 | 0.333 | 0.8777 | 0.7623 | 5 | 5 | 12.03 | 110.0 |
| SEASON_2024_2026 | COMPLETED | 98 | 4/10 | 0.250 | 0.8124 | 0.6625 | 6 | 6 | 24.00 | 118.0 |

### Supplementary scenarios

| Scenario | Status | Eligible | Top-10 overlap | Jaccard | Spearman | Kendall | Entrants | Leavers | Mean |Δrank| | Max |Δrank| |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SUPP_SIGMA_8 | COMPLETED_SUPPLEMENTARY | 134 | 6/10 | 0.429 | 0.9432 | 0.8230 | 4 | 4 | 9.43 | 78.0 |
| SUPP_SIGMA_10 | COMPLETED_SUPPLEMENTARY | 140 | 7/10 | 0.538 | 0.9754 | 0.8809 | 3 | 3 | 5.87 | 55.0 |
| SUPP_SIGMA_15 | COMPLETED_SUPPLEMENTARY | 143 | 8/10 | 0.667 | 0.9783 | 0.8812 | 2 | 2 | 6.09 | 32.0 |
| SUPP_SIGMA_20 | COMPLETED_SUPPLEMENTARY | 158 | 7/10 | 0.538 | 0.9423 | 0.7990 | 3 | 3 | 13.06 | 56.0 |
| SUPP_H_LINEAR | COMPLETED_SUPPLEMENTARY | 137 | 6/10 | 0.429 | 0.9212 | 0.7742 | 4 | 4 | 11.33 | 61.0 |
| SUPP_H_QUADRATIC | COMPLETED_SUPPLEMENTARY | 130 | 3/10 | 0.176 | 0.8519 | 0.6628 | 7 | 7 | 17.91 | 68.0 |
| SUPP_LEVERAGE_0 | COMPLETED_SUPPLEMENTARY | 141 | 9/10 | 0.818 | 0.9988 | 0.9880 | 1 | 1 | 0.81 | 15.0 |
| SUPP_LEVERAGE_1_5 | COMPLETED_SUPPLEMENTARY | 141 | 9/10 | 0.818 | 0.9999 | 0.9968 | 1 | 1 | 0.23 | 6.0 |
| SUPP_LEVERAGE_5 | COMPLETED_SUPPLEMENTARY | 141 | 10/10 | 1.000 | 1.0000 | 0.9986 | 0 | 0 | 0.10 | 2.0 |
| SUPP_WIDE_STUMP_REMOVED | COMPLETED_SUPPLEMENTARY | 141 | 10/10 | 1.000 | 1.0000 | 0.9990 | 0 | 0 | 0.07 | 4.0 |

### Most stable primary top-10 bowlers

| Player | Primary rank | Top-10 appearances | Mean |Δrank| | Max |Δrank| | Worst scenario | Mean |ΔZ| |
| --- | --- | --- | --- | --- | --- | --- |
| 4658 Nasum Ahmed | 1 | 19/19 | 0.11 | 2.0 | SEASON_EQUAL | 0.0595 |
| 4840 Odean Smith | 2 | 16/16 | 0.38 | 4.0 | SEASON_EQUAL | 0.0443 |
| 7690 Saim Ayub | 4 | 19/19 | 0.58 | 5.0 | SEASON_EQUAL | 0.0358 |
| 7364 Haris Rauf | 3 | 20/20 | 0.65 | 4.0 | SEASON_EQUAL | 0.0374 |
| 7699 Abbas Afridi | 6 | 19/20 | 0.75 | 6.0 | SEASON_EQUAL | 0.0197 |
| 6643 Hasan Mahmud | 9 | 13/16 | 1.19 | 9.0 | P_55 | 0.0343 |
| 781 Sunil Narine | 5 | 19/20 | 1.20 | 14.0 | SEASON_2024_2026 | 0.0505 |
| 7503 Ravi Bishnoi | 8 | 17/20 | 1.85 | 12.0 | SEASON_2024_2026 | 0.0576 |

### Most sensitive primary top-10 bowlers

| Player | Primary rank | Top-10 appearances | Mean |Δrank| | Max |Δrank| | Worst scenario | Mean |ΔZ| |
| --- | --- | --- | --- | --- | --- | --- |
| 1596 Moeen Ali | 7 | 14/17 | 4.53 | 41.0 | P_55 | 0.1072 |
| 8661 Matheesha Pathirana | 10 | 14/20 | 2.90 | 25.0 | SEASON_EQUAL | 0.0729 |
| 7503 Ravi Bishnoi | 8 | 17/20 | 1.85 | 12.0 | SEASON_2024_2026 | 0.0576 |
| 781 Sunil Narine | 5 | 19/20 | 1.20 | 14.0 | SEASON_2024_2026 | 0.0505 |
| 6643 Hasan Mahmud | 9 | 13/16 | 1.19 | 9.0 | P_55 | 0.0343 |
| 7699 Abbas Afridi | 6 | 19/20 | 0.75 | 6.0 | SEASON_EQUAL | 0.0197 |
| 7364 Haris Rauf | 3 | 20/20 | 0.65 | 4.0 | SEASON_EQUAL | 0.0374 |
| 7690 Saim Ayub | 4 | 19/19 | 0.58 | 5.0 | SEASON_EQUAL | 0.0358 |

### Largest bowler rank movements across approved scenarios

| Player | Primary rank | Top-10 appearances | Mean |Δrank| | Max |Δrank| | Worst scenario | Mean |ΔZ| |
| --- | --- | --- | --- | --- | --- | --- |
| 1596 Moeen Ali | 7 | 14/17 | 4.53 | 41.0 | P_55 | 0.1072 |
| 8661 Matheesha Pathirana | 10 | 14/20 | 2.90 | 25.0 | SEASON_EQUAL | 0.0729 |
| 781 Sunil Narine | 5 | 19/20 | 1.20 | 14.0 | SEASON_2024_2026 | 0.0505 |
| 7503 Ravi Bishnoi | 8 | 17/20 | 1.85 | 12.0 | SEASON_2024_2026 | 0.0576 |
| 6643 Hasan Mahmud | 9 | 13/16 | 1.19 | 9.0 | P_55 | 0.0343 |
| 7699 Abbas Afridi | 6 | 19/20 | 0.75 | 6.0 | SEASON_EQUAL | 0.0197 |
| 7690 Saim Ayub | 4 | 19/19 | 0.58 | 5.0 | SEASON_EQUAL | 0.0358 |
| 4840 Odean Smith | 2 | 16/16 | 0.38 | 4.0 | SEASON_EQUAL | 0.0443 |
| 7364 Haris Rauf | 3 | 20/20 | 0.65 | 4.0 | SEASON_EQUAL | 0.0374 |
| 4658 Nasum Ahmed | 1 | 19/19 | 0.11 | 2.0 | SEASON_EQUAL | 0.0595 |

---

## 6. Top-10 overlap and correlation tables

### Batter top-10 stability

| Scenario | Status | Eligible | Top-10 overlap | Jaccard | Spearman | Kendall | Entrants | Leavers | Mean |Δrank| | Max |Δrank| |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRIMARY | PRIMARY | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| P_55 | COMPLETED | 108 | 7/10 | 0.538 | 0.9444 | 0.8052 | 3 | 3 | 8.07 | 40.0 |
| P_65 | COMPLETED | 93 | 7/10 | 0.538 | 0.9357 | 0.8023 | 3 | 3 | 7.25 | 43.0 |
| K_25 | COMPLETED | 101 | 10/10 | 1.000 | 0.9987 | 0.9774 | 0 | 0 | 0.97 | 5.0 |
| K_100 | COMPLETED | 101 | 9/10 | 0.818 | 0.9969 | 0.9608 | 1 | 1 | 1.58 | 8.0 |
| NRAW_50 | COMPLETED | 104 | 10/10 | 1.000 | 0.9923 | 0.9770 | 0 | 0 | 1.50 | 32.0 |
| NRAW_100 | COMPLETED | 96 | 9/10 | 0.818 | 0.9988 | 0.9930 | 1 | 1 | 1.05 | 12.0 |
| WKT_RATE_NEFF_ALL_DELIVERIES | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| DISMISSAL_RATE_WIDE_EXCLUDED | COMPLETED | 101 | 10/10 | 1.000 | 0.9998 | 0.9956 | 0 | 0 | 0.22 | 4.0 |
| BOUNDARY_RUNS_PROXY | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 0.9988 | 0 | 0 | 0.06 | 2.0 |
| OTHER_BOUNDARY_LEGAL_OVERSTEP | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| OTHER_BOUNDARY_LEGAL_ONLY | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| OTHER_AS_LEGAL | COMPLETED | 101 | 9/10 | 0.818 | 0.9999 | 0.9976 | 1 | 1 | 0.12 | 1.0 |
| FORMAT_WEIGHT_NEFF_PROPORTIONAL | COMPLETED | 101 | 9/10 | 0.818 | 0.9871 | 0.9450 | 1 | 1 | 2.22 | 29.0 |
| CRR_FIRST_INNINGS | COMPLETED | 101 | 8/10 | 0.667 | 0.9913 | 0.9329 | 2 | 2 | 2.77 | 16.0 |
| ELIG_M_ALL | COMPLETED | 103 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.73 | 2.0 |
| ELIG_PER_FORMAT_M10 | COMPLETED | 101 | 9/10 | 0.818 | 0.9916 | 0.9798 | 1 | 1 | 1.01 | 35.0 |
| NEFF_SCOPE_ALL_DELIVERIES | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| MATCH_48610_P1_FALLBACK | COMPLETED | 101 | 10/10 | 1.000 | 1.0000 | 0.9996 | 0 | 0 | 0.02 | 1.0 |
| SEASON_EQUAL | COMPLETED | 98 | 8/10 | 0.667 | 0.8916 | 0.7766 | 2 | 2 | 7.82 | 57.0 |
| SEASON_2024_2026 | COMPLETED | 52 | 3/10 | 0.176 | 0.7624 | 0.6169 | 7 | 7 | 24.00 | 73.0 |

### Bowler top-10 stability

| Scenario | Status | Eligible | Top-10 overlap | Jaccard | Spearman | Kendall | Entrants | Leavers | Mean |Δrank| | Max |Δrank| |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRIMARY | PRIMARY | 141 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| P_55 | COMPLETED | 146 | 8/10 | 0.667 | 0.9744 | 0.8843 | 2 | 2 | 6.67 | 54.0 |
| P_65 | COMPLETED | 133 | 6/10 | 0.429 | 0.9722 | 0.8693 | 4 | 4 | 7.85 | 59.0 |
| K_25 | COMPLETED | 141 | 10/10 | 1.000 | 0.9987 | 0.9757 | 0 | 0 | 1.50 | 7.0 |
| K_100 | COMPLETED | 141 | 8/10 | 0.667 | 0.9972 | 0.9572 | 2 | 2 | 2.41 | 8.0 |
| NRAW_50 | COMPLETED | 145 | 9/10 | 0.818 | 0.9880 | 0.9550 | 1 | 1 | 2.57 | 38.0 |
| NRAW_100 | COMPLETED | 126 | 6/10 | 0.429 | 0.9739 | 0.9451 | 4 | 4 | 8.97 | 61.0 |
| WKT_RATE_NEFF_ALL_DELIVERIES | COMPLETED | 141 | 10/10 | 1.000 | 1.0000 | 0.9982 | 0 | 0 | 0.13 | 2.0 |
| DISMISSAL_RATE_WIDE_EXCLUDED | COMPLETED | 141 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| BOUNDARY_RUNS_PROXY | COMPLETED | 141 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 0.00 | 0.0 |
| OTHER_BOUNDARY_LEGAL_OVERSTEP | COMPLETED | 141 | 10/10 | 1.000 | 1.0000 | 0.9986 | 0 | 0 | 0.10 | 2.0 |
| OTHER_BOUNDARY_LEGAL_ONLY | COMPLETED | 141 | 10/10 | 1.000 | 0.9999 | 0.9976 | 0 | 0 | 0.17 | 2.0 |
| OTHER_AS_LEGAL | COMPLETED | 141 | 10/10 | 1.000 | 0.9997 | 0.9913 | 0 | 0 | 0.58 | 3.0 |
| FORMAT_WEIGHT_NEFF_PROPORTIONAL | COMPLETED | 141 | 9/10 | 0.818 | 0.9868 | 0.9449 | 1 | 1 | 2.95 | 45.0 |
| CRR_FIRST_INNINGS | COMPLETED | 142 | 6/10 | 0.429 | 0.9760 | 0.8808 | 4 | 4 | 6.04 | 56.0 |
| ELIG_M_ALL | COMPLETED | 146 | 10/10 | 1.000 | 1.0000 | 1.0000 | 0 | 0 | 2.42 | 5.0 |
| ELIG_PER_FORMAT_M10 | COMPLETED | 139 | 9/10 | 0.818 | 0.9778 | 0.9566 | 1 | 1 | 2.71 | 67.0 |
| NEFF_SCOPE_ALL_DELIVERIES | COMPLETED | 141 | 10/10 | 1.000 | 0.9999 | 0.9959 | 0 | 0 | 0.27 | 2.0 |
| MATCH_48610_P1_FALLBACK | COMPLETED | 141 | 10/10 | 1.000 | 0.9997 | 0.9968 | 0 | 0 | 0.23 | 10.0 |
| SEASON_EQUAL | COMPLETED | 131 | 5/10 | 0.333 | 0.8777 | 0.7623 | 5 | 5 | 12.03 | 110.0 |
| SEASON_2024_2026 | COMPLETED | 98 | 4/10 | 0.250 | 0.8124 | 0.6625 | 6 | 6 | 24.00 | 118.0 |

### Top-10 entrants and leavers in selected scenarios

| Role | Scenario | Entrants | Leavers | Overlap | Spearman |
| --- | --- | --- | --- | --- | --- |
| batter | P_55 | 768 Reeza Hendricks, 2671 Liton Das, 4986 Rovman Powell | 2930 Rassie van der Dussen, 4246 Nitish Rana, 6651 Towhid Hridoy | 7/10 | 0.9444 |
| batter | P_65 | 813 Jos Buttler, 6725 Sherfane Rutherford, 535 Ambati Rayudu | 2930 Rassie van der Dussen, 4246 Nitish Rana, 6651 Towhid Hridoy | 7/10 | 0.9357 |
| batter | K_25 | — | — | 10/10 | 0.9987 |
| batter | K_100 | 2984 Sikandar Raza | 6651 Towhid Hridoy | 9/10 | 0.9969 |
| batter | NRAW_50 | — | — | 10/10 | 0.9923 |
| batter | NRAW_100 | 813 Jos Buttler | 6651 Towhid Hridoy | 9/10 | 0.9988 |
| batter | OTHER_AS_LEGAL | 2984 Sikandar Raza | 6651 Towhid Hridoy | 9/10 | 0.9999 |
| batter | FORMAT_WEIGHT_NEFF_PROPORTIONAL | 813 Jos Buttler | 1699 Suryakumar Yadav | 9/10 | 0.9871 |
| batter | CRR_FIRST_INNINGS | 2671 Liton Das, 2984 Sikandar Raza | 2930 Rassie van der Dussen, 6651 Towhid Hridoy | 8/10 | 0.9913 |
| batter | ELIG_PER_FORMAT_M10 | 813 Jos Buttler | 6651 Towhid Hridoy | 9/10 | 0.9916 |
| batter | MATCH_48610_P1_FALLBACK | — | — | 10/10 | 1.0000 |
| batter | SEASON_EQUAL | 3024 Mohammad Rizwan, 6725 Sherfane Rutherford | 2485 Babar Azam, 1699 Suryakumar Yadav | 8/10 | 0.8916 |
| batter | SEASON_2024_2026 | 4986 Rovman Powell, 2984 Sikandar Raza, 6423 Riyan Parag, 6396 Tim David, 813 Jos Buttler, 6460 Ayush Badoni, 3647 Shreyas Iyer | 3374 Mark Chapman, 4369 Shai Hope, 6288 Shubman Gill, 2485 Babar Azam, 2930 Rassie van der Dussen, 1699 Suryakumar Yadav, 4246 Nitish Rana | 3/10 | 0.7624 |
| bowler | P_55 | 7920 Nathan Ellis, 3720 Craig Young | 1596 Moeen Ali, 6643 Hasan Mahmud | 8/10 | 0.9744 |
| bowler | P_65 | 829 Mitchell Starc, 278 Tim Southee, 3720 Craig Young, 7920 Nathan Ellis | 4840 Odean Smith, 1596 Moeen Ali, 6643 Hasan Mahmud, 8661 Matheesha Pathirana | 6/10 | 0.9722 |
| bowler | K_25 | — | — | 10/10 | 0.9987 |
| bowler | K_100 | 7920 Nathan Ellis, 3720 Craig Young | 6643 Hasan Mahmud, 8661 Matheesha Pathirana | 8/10 | 0.9972 |
| bowler | NRAW_50 | 3720 Craig Young | 1596 Moeen Ali | 9/10 | 0.9880 |
| bowler | NRAW_100 | 39657 Eshan Malinga, 3720 Craig Young, 7920 Nathan Ellis, 278 Tim Southee | 4840 Odean Smith, 7690 Saim Ayub, 1596 Moeen Ali, 6643 Hasan Mahmud | 6/10 | 0.9739 |
| bowler | OTHER_AS_LEGAL | — | — | 10/10 | 0.9997 |
| bowler | FORMAT_WEIGHT_NEFF_PROPORTIONAL | 3720 Craig Young | 8661 Matheesha Pathirana | 9/10 | 0.9868 |
| bowler | CRR_FIRST_INNINGS | 278 Tim Southee, 2490 Mohammad Nawaz, 5837 Mahedi Hasan, 829 Mitchell Starc | 4840 Odean Smith, 7503 Ravi Bishnoi, 6643 Hasan Mahmud, 8661 Matheesha Pathirana | 6/10 | 0.9760 |
| bowler | ELIG_PER_FORMAT_M10 | 39657 Eshan Malinga | 8661 Matheesha Pathirana | 9/10 | 0.9778 |
| bowler | MATCH_48610_P1_FALLBACK | — | — | 10/10 | 0.9997 |
| bowler | SEASON_EQUAL | 1944 Keshav Maharaj, 4900 Wanindu Hasaranga, 278 Tim Southee, 22920 Jacob Duffy, 5379 Mark Adair | 7699 Abbas Afridi, 1596 Moeen Ali, 7503 Ravi Bishnoi, 6643 Hasan Mahmud, 8661 Matheesha Pathirana | 5/10 | 0.8777 |
| bowler | SEASON_2024_2026 | 7920 Nathan Ellis, 2681 Taskin Ahmed, 3644 Kuldeep Yadav, 7344 Shoriful Islam, 2633 Jason Holder, 5837 Mahedi Hasan | 4658 Nasum Ahmed, 4840 Odean Smith, 781 Sunil Narine, 1596 Moeen Ali, 7503 Ravi Bishnoi, 6643 Hasan Mahmud | 4/10 | 0.8124 |

---

## 7. Important player movements

The table below lists the largest approved-scenario rank movements among players with at least ten approved comparisons. A positive rank change is a drop; a negative change is an improvement. Primary rank is shown for context.

**Batters — largest absolute rank movements**

| Player | Primary rank | Top-10 appearances | Mean |Δrank| | Max |Δrank| | Worst scenario | Mean |ΔZ| |
| --- | --- | --- | --- | --- | --- | --- |
| 4106 Daryl Mitchell | 87 | 0/20 | 6.80 | 73.0 | SEASON_2024_2026 | 0.1024 |
| 4409 Sam Curran | 82 | 0/20 | 4.35 | 57.0 | SEASON_2024_2026 | 0.0513 |
| 6512 Michael Bracewell | 101 | 0/20 | 6.55 | 57.0 | SEASON_EQUAL | 0.1660 |
| 4812 Harry Tector | 27 | 0/19 | 3.58 | 55.0 | SEASON_EQUAL | 0.0755 |
| 6676 Azmatullah Omarzai | 80 | 0/20 | 4.30 | 48.0 | SEASON_2024_2026 | 0.0463 |
| 3489 Salman Agha | 94 | 0/20 | 3.95 | 47.0 | SEASON_2024_2026 | 0.0244 |
| 49003 Hasan Nawaz | 98 | 0/18 | 3.39 | 47.0 | SEASON_2024_2026 | 0.0314 |
| 5882 Afif Hossain | 38 | 0/19 | 3.58 | 46.0 | SEASON_EQUAL | 0.0751 |
| 25213 Dewald Brevis | 96 | 0/18 | 3.28 | 46.0 | SEASON_2024_2026 | 0.0780 |
| 5939 Cameron Green | 90 | 0/20 | 4.05 | 44.0 | SEASON_2024_2026 | 0.0415 |

**Bowlers — largest absolute rank movements**

| Player | Primary rank | Top-10 appearances | Mean |Δrank| | Max |Δrank| | Worst scenario | Mean |ΔZ| |
| --- | --- | --- | --- | --- | --- | --- |
| 7240 FazalHaq Farooqi | 136 | 0/20 | 9.70 | 118.0 | SEASON_2024_2026 | 0.1689 |
| 5379 Mark Adair | 120 | 1/20 | 11.70 | 110.0 | SEASON_EQUAL | 0.1661 |
| 3628 Kagiso Rabada | 125 | 0/20 | 7.75 | 100.0 | SEASON_2024_2026 | 0.1178 |
| 8049 Naseem Shah | 113 | 0/19 | 7.21 | 76.0 | SEASON_EQUAL | 0.1018 |
| 1487 Adam Milne | 31 | 0/19 | 5.42 | 69.0 | SEASON_EQUAL | 0.0745 |
| 5939 Cameron Green | 86 | 0/20 | 7.30 | 69.0 | SEASON_2024_2026 | 0.0846 |
| 58246 Prince Yadav | 114 | 0/20 | 8.70 | 67.0 | ELIG_PER_FORMAT_M10 | 0.0906 |
| 7344 Shoriful Islam | 29 | 1/20 | 5.20 | 62.0 | SEASON_EQUAL | 0.0762 |
| 2933 Jasprit Bumrah | 77 | 0/20 | 18.00 | 61.0 | NRAW_100 | 0.2358 |
| 8295 Matthew Forde | 89 | 0/20 | 5.35 | 60.0 | SEASON_2024_2026 | 0.0625 |

---

## 8. Eligibility changes

| Scenario | Role | Primary eligible | Scenario eligible | Δ | Common | Newly eligible | No longer eligible |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BOUNDARY_RUNS_PROXY | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| BOUNDARY_RUNS_PROXY | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| CRR_FIRST_INNINGS | batter | 101 | 101 | 0 | 100 | 1 | 1 |
| CRR_FIRST_INNINGS | bowler | 141 | 142 | 1 | 140 | 2 | 1 |
| DISMISSAL_RATE_WIDE_EXCLUDED | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| DISMISSAL_RATE_WIDE_EXCLUDED | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| ELIG_M_ALL | batter | 101 | 103 | 2 | 101 | 2 | 0 |
| ELIG_M_ALL | bowler | 141 | 146 | 5 | 141 | 5 | 0 |
| ELIG_PER_FORMAT_M10 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| ELIG_PER_FORMAT_M10 | bowler | 141 | 139 | -2 | 139 | 0 | 2 |
| FORMAT_WEIGHT_NEFF_PROPORTIONAL | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| FORMAT_WEIGHT_NEFF_PROPORTIONAL | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| K_100 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| K_100 | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| K_25 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| K_25 | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| MATCH_48610_P1_FALLBACK | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| MATCH_48610_P1_FALLBACK | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| NEFF_SCOPE_ALL_DELIVERIES | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| NEFF_SCOPE_ALL_DELIVERIES | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| NRAW_100 | batter | 101 | 96 | -5 | 96 | 0 | 5 |
| NRAW_100 | bowler | 141 | 126 | -15 | 126 | 0 | 15 |
| NRAW_50 | batter | 101 | 104 | 3 | 101 | 3 | 0 |
| NRAW_50 | bowler | 141 | 145 | 4 | 141 | 4 | 0 |
| OTHER_AS_LEGAL | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| OTHER_AS_LEGAL | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| OTHER_BOUNDARY_LEGAL_ONLY | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| OTHER_BOUNDARY_LEGAL_ONLY | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| OTHER_BOUNDARY_LEGAL_OVERSTEP | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| OTHER_BOUNDARY_LEGAL_OVERSTEP | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| PRIMARY | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| PRIMARY | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| P_55 | batter | 101 | 108 | 7 | 95 | 13 | 6 |
| P_55 | bowler | 141 | 146 | 5 | 140 | 6 | 1 |
| P_65 | batter | 101 | 93 | -8 | 89 | 4 | 12 |
| P_65 | bowler | 141 | 133 | -8 | 132 | 1 | 9 |
| SEASON_2024_2026 | batter | 101 | 52 | -49 | 52 | 0 | 49 |
| SEASON_2024_2026 | bowler | 141 | 98 | -43 | 98 | 0 | 43 |
| SEASON_EQUAL | batter | 101 | 98 | -3 | 98 | 0 | 3 |
| SEASON_EQUAL | bowler | 141 | 131 | -10 | 131 | 0 | 10 |
| SUPP_H_LINEAR | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_H_LINEAR | bowler | 141 | 137 | -4 | 133 | 4 | 8 |
| SUPP_H_QUADRATIC | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_H_QUADRATIC | bowler | 141 | 130 | -11 | 127 | 3 | 14 |
| SUPP_LEVERAGE_0 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_LEVERAGE_0 | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| SUPP_LEVERAGE_1_5 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_LEVERAGE_1_5 | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| SUPP_LEVERAGE_5 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_LEVERAGE_5 | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| SUPP_SIGMA_10 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_SIGMA_10 | bowler | 141 | 140 | -1 | 139 | 1 | 2 |
| SUPP_SIGMA_15 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_SIGMA_15 | bowler | 141 | 143 | 2 | 140 | 3 | 1 |
| SUPP_SIGMA_20 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_SIGMA_20 | bowler | 141 | 158 | 17 | 140 | 18 | 1 |
| SUPP_SIGMA_8 | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_SIGMA_8 | bowler | 141 | 134 | -7 | 133 | 1 | 8 |
| SUPP_WIDE_STUMP_REMOVED | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| SUPP_WIDE_STUMP_REMOVED | bowler | 141 | 141 | 0 | 141 | 0 | 0 |
| WKT_RATE_NEFF_ALL_DELIVERIES | batter | 101 | 101 | 0 | 101 | 0 | 0 |
| WKT_RATE_NEFF_ALL_DELIVERIES | bowler | 141 | 141 | 0 | 141 | 0 | 0 |

Eligibility changes are concentrated in the gates that alter the match-breadth or sample requirements: `NRAW_50`, `NRAW_100`, `ELIG_M_ALL`, `ELIG_PER_FORMAT_M10`, `SEASON_EQUAL` and `SEASON_2024_2026`. Scenarios that change only measurement definitions or pressure features leave the primary eligible population intact unless a reclassification moves a player across the $N_{raw}$ or $N_{eff}$ boundary.

---

## 9. Limitations and interpretation

1. **Reference moments and calibration.** Sensitivity results hold the approved peer means, reference moments and calibration constants fixed, except for the two metric-definition sensitivities for which Stage 4.2 publishes alternative moments (dismissal Definition B and the runs-proxy batter boundary). Re-estimating all moments inside every scenario would confound the parameter change with a recalibration and is not the approved comparison.
2. **Season-equal and 2024–2026 are evidence-base changes.** They change which seasons and how much weight each season contributes. Their lower correlations are expected and are not evidence that the primary formula is wrong. They do show that the ranking is not season-invariant.
3. **Small-season leverage.** Season-equal weighting gives each format-season equal total weight, including short seasons such as T20I 2023/24 and 2024/25. This can materially change player-level estimates.
4. **Top-10 overlap is discrete.** A swap between rank 10 and rank 11 changes overlap by one even when the global rank correlation is very high. Overlap is therefore reported alongside Spearman and Kendall, never instead of them.
5. **Supplementary scenarios are not approved methodology.** The $\sigma_S$ alternatives (8/10/15/20), linear/quadratic wicket-remaining functions, leverage alternatives (0/1.5/5) and removal of wide stumpings are diagnostics only. They cannot change the primary ranking and should not be presented as approved alternatives.
6. **Capped $N_{eff}$ weighting is not run.** No numeric cap $C$ is registered; running it without $C$ would fabricate a parameter.
7. **Baseline exposure is blocked.** Any alternative to the 120-ball exposure rule must be pre-registered; none is.
8. **Correlation populations differ by scenario.** Spearman and Kendall use only players eligible in both the primary and the scenario. The common population size is reported in every stability table.
9. **Rank changes are not performance changes.** A rank movement can reflect another player's movement or an eligibility change, not a change in the player's own estimated quality.

---

## 10. Final conclusion on ranking robustness

The approved Stage 5 rankings are **robust to the approved parameter grid**. All six Section 13.1 alternatives exceed the $\rho>0.92$ target in both roles (minimum batter 0.9357, minimum bowler 0.9722). Top-10 **membership** is unchanged under $K=25$ for both roles and changes by at most four members under any approved Section 13.1 grid alternative. Individual rank movements can be substantially larger; the mean and maximum $|\Delta rank|$ columns in the detailed tables quantify those movements.

The rankings are also stable under the main measurement-definition alternatives: `other` boundary treatments, `OTHER_AS_LEGAL`, dismissal Definition B, the batter runs-proxy boundary source, $N_{eff}$ scope, $N_{eff}$-proportional cross-format weighting, first-innings CRR, $M_{all}$, per-format $M\ge10$ and the Match 48610 P1 fallback. Only 2 approved non-grid scenarios fall below 0.92: SEASON_2024_2026, SEASON_EQUAL.

The ranking is **not season-invariant**. Season-equal weighting and the 2024–2026-only restriction produce materially lower correlations and much lower top-10 overlap, particularly for bowlers. This is the principal robustness limitation. It should be carried forward as a documented scope limitation: the primary ranking describes the approved 2022–2026 pooled evidence base, not a claim that the same ten players would rank identically in a recent-seasons-only or season-equal world.

**Verdict:** Stage 6 is complete. The primary rankings remain unchanged and are robust to the approved sensitivity grid and the approved measurement alternatives. The season-weighting and recent-seasons sensitivities are unfavorable but valid results and are reported without suppression.

---

## 11. Validation

Independent Stage 6 validation: **23/23 checks passed**. The validation layer re-read the generated CSVs and independently recomputed top-10 overlap, Jaccard, Spearman, Kendall, entrant/leaver lists and eligibility changes. It also verified that the primary scores and ranks reproduce Stage 5, that the input hashes are unchanged, that eligible scores are finite, that player-role-scenario keys are unique and that every mandatory scenario is completed or explicitly labelled.

All checks passed. See `outputs/stage6/stage6_validation_checks.csv` for the full list.

---

## 12. Outputs

- `outputs/stage6/sensitivity_summary.csv`
- `outputs/stage6/batter_sensitivity_rankings.csv`
- `outputs/stage6/bowler_sensitivity_rankings.csv`
- `outputs/stage6/batter_top10_stability.csv`
- `outputs/stage6/bowler_top10_stability.csv`
- `outputs/stage6/eligibility_sensitivity.csv`
- `outputs/stage6/player_rank_changes.csv`
- `outputs/stage6/stage6_validation_checks.csv` (supporting validation log)
- `reports/stage6_sensitivity_report.md`


No raw dataset, approved pressure-feature dataset, Stage 5 scoring output or Stage 5 validation output was modified. No dashboard was built as part of Stage 6; the Stage 7 dashboard is a read-only presentation layer over these approved outputs.
