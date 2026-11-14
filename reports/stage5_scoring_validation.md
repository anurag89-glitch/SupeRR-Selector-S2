# Stage 5 Primary Scoring — Validation Report

**Scope:** approved Stage 4.2 pressure metrics, format-level eligibility, Kish effective sample size, \(K=50\) shrinkage, equal-weight cross-format composite, calibrated reliability, deterministic tie-breaks, and the final \(M_{role}\ge10\) gate.

**Overall status: PASS**

**Scoring corpus:** 191,963 deliveries / 812 matches.  **Audit corpus:** 192,056 deliveries.  **Checks:** 70 total, 70 passed, 0 failed.

The full check list is in Section 7.  The headline sections below show the reconciled corpus, pressure-engine reproduction, eligible populations, calibration moments and final top-10 lists.

## 1. Corpus and data-rule reconciliation

| Quantity | Observed | Approved / expected | Status |
| --- | --- | --- | --- |
| Audit deliveries | 192,056 | 192,056 | PASS |
| Scoring deliveries | 191,963 | 191,963 | PASS |
| Scoring matches | 812 | 812 | PASS |
| T20 (IPL) deliveries | 87,217 | 87,217 | PASS |
| T20I deliveries | 104,746 | 104,746 | PASS |
| Match 48610 first innings | 101 | 101 | PASS |
| Match 48610 chase excluded | 93 | 93 | PASS |
| `other` extras in scoring corpus | 256 | 256 | PASS |

The 11-boundary audit-to-scoring difference is entirely the excluded Match 48610 chase: 9,827 audit / 9,816 scoring under the provisional all-extras rule.  The verified-core counts are 9,801 / 9,790, and legal-only counts are 9,767 / 9,756.

## 2. Pressure-engine reproduction

The eight approved canonical scenarios were independently recomputed from the Stage 4.2 equations.  Maximum absolute deviation across P_bat and P_bowl is **0.0498** points against the documented one-decimal values.

| Scenario | P_bat expected | P_bat observed | P_bowl expected | P_bowl observed |
| --- | --- | --- | --- | --- |
| S1 | 75.3 | 75.26 | 23.0 | 23.04 |
| S2 | 94.0 | 94.05 | 1.8 | 1.76 |
| S3 | 86.4 | 86.36 | 98.1 | 98.14 |
| S4 | 17.5 | 17.49 | 4.3 | 4.30 |
| S5 | 99.2 | 99.21 | 1.6 | 1.62 |
| S6 | 88.0 | 87.98 | 79.3 | 79.29 |
| S7 | 79.2 | 79.18 | 49.3 | 49.28 |
| S8 | 48.5 | 48.52 | 83.0 | 82.99 |

## 3. Eligible populations and calibration

| Role | F records | F players | Final records | Final players | Calibration n | M_role<10 players |
| --- | --- | --- | --- | --- | --- | --- |
| Batter | 144 | 122 | 123 | 101 | 122 | 21 |
| Bowler | 209 | 173 | 177 | 141 | 173 | 32 |

The calibration population is \(F_{j,r}\neq\varnothing\) for each role and does **not** apply the \(M_{role}\ge10\) gate.  It therefore includes the 21 batter and 32 bowler players excluded from the final rankings by match breadth.

| Role | n | Recomputed mu | Approved mu | Recomputed sigma | Approved sigma |
| --- | --- | --- | --- | --- | --- |
| Batter | 122 | 0.1036068081 | 0.1036068081 | 0.6610638828 | 0.6610638828 |
| Bowler | 173 | 0.0256919706 | 0.0256919707 | 0.6655792246 | 0.6655792246 |

**Both-role final-eligible players:** 23 (approved 23).  Batter and bowler rankings are separate; no combined all-rounder primary ranking is produced.

## 4. Final top 10 batters

| Rank | Player ID | Player | F formats | M_role | Z_comp | Reliability |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 3374 | Mark Chapman | T20I | 24 | 1.5480186610 | 85.1698419935 |
| 2 | 4369 | Shai Hope | T20I | 13 | 1.4264533669 | 83.2139925272 |
| 3 | 6288 | Shubman Gill | IPL | 14 | 1.3655960416 | 82.1599514098 |
| 4 | 37052 | Naman Dhir | IPL | 15 | 1.3304305976 | 81.5276309322 |
| 5 | 2485 | Babar Azam | T20I | 13 | 1.3146730358 | 81.2387168837 |
| 6 | 2930 | Rassie van der Dussen | T20I | 10 | 1.1912699846 | 78.8558440598 |
| 7 | 1699 | Suryakumar Yadav | IPL,T20I | 47 | 1.1498883982 | 78.0087971240 |
| 8 | 2921 | Fakhar Zaman | T20I | 20 | 1.1325605715 | 77.6469496962 |
| 9 | 4246 | Nitish Rana | IPL | 26 | 1.1285850098 | 77.5633348381 |
| 10 | 6651 | Towhid Hridoy | T20I | 22 | 0.9880464986 | 74.4658300455 |

## 5. Final top 10 bowlers

| Rank | Player ID | Player | F formats | M_role | Z_comp | Reliability |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 4658 | Nasum Ahmed | T20I | 11 | 1.6694664847 | 87.8227614326 |
| 2 | 4840 | Odean Smith | T20I | 10 | 1.4370259325 | 84.5059753997 |
| 3 | 7364 | Haris Rauf | T20I | 30 | 1.2993490499 | 82.2135853920 |
| 4 | 7690 | Saim Ayub | T20I | 11 | 1.2823561045 | 81.9129482658 |
| 5 | 781 | Sunil Narine | IPL | 30 | 1.2321671355 | 81.0019302911 |
| 6 | 7699 | Abbas Afridi | T20I | 18 | 1.1715183070 | 79.8547061265 |
| 7 | 1596 | Moeen Ali | T20I | 12 | 1.1226701322 | 78.8936120739 |
| 8 | 7503 | Ravi Bishnoi | IPL,T20I | 47 | 1.0494806930 | 77.3915470113 |
| 9 | 6643 | Hasan Mahmud | T20I | 10 | 1.0116660024 | 76.5863904501 |
| 10 | 8661 | Matheesha Pathirana | IPL,T20I | 29 | 1.0002874149 | 76.3402552168 |

## 6. Method-fidelity notes

- Pressure cutoff: \(P\ge60\), weight \(=(P/100)^2\).  Format gates: \(N_{raw}\ge75\), \(N_{eff,del}\ge35\).  Batter baseline: at least 120 balls faced and 120 legal balls.  Bowler baseline: at least 120 legal balls.
- Approved weights: 30/25/20/15/10 for both roles.  Bowler signs: \(+0.30\Delta Econ\), \(-0.25 Econ_P\), \(+0.20 WktRate_P\), \(+0.15 Dot\%_{bowl,P}\), \(-0.10 BoundaryConcededRate_P\).
- Kish \(N_{eff}\) uses delivery-level weights; shrinkage uses \(K=50\); z-scores use the approved format-specific population moments; cross-format aggregation is an equal-weight mean over \(F_{j,r}\).
- Reliability is \(100/(1+\exp(-0.80\,Z_{std}))\) with the approved per-role \(\mu_{Zcomp}\) and \(\sigma_{Zcomp}\).
- Final ranking order is Z_comp desc, summed \(N_{eff,del}\) over F desc, M_role desc, summed N_raw over F desc, player_id asc.  The final gate is \(F_{j,r}\neq\varnothing\) and \(M_{role}\ge10\).
- Match 48610's 93 second-innings rows are excluded from both pressure and personal baselines; its 101 first-innings rows remain.  `other` remains provisional no-ball-like (`PROVISIONAL_OTHER`); no unresolved extra was silently reclassified.
- Capped \(N_{eff}\)-proportional cross-format weighting is optional and was **not** used in primary scoring.  Equal format weighting is primary.

## 7. Full check list

| # | Area | Check | Result | Detail |
| --- | --- | --- | --- | --- |
| 1 | Corpus | Audit corpus row count | PASS | 192,056 observed / 192,056 approved |
| 2 | Corpus | Scoring corpus row count | PASS | 191,963 observed / 191,963 approved |
| 3 | Corpus | Scoring corpus match count | PASS | 812 matches |
| 4 | Corpus | Format row counts | PASS | T20=87,217; T20I=104,746 |
| 5 | Match 48610 | Retain 101 first-innings deliveries | PASS | 101 first-innings rows |
| 6 | Match 48610 | Identify 93 excluded second-innings deliveries | PASS | 93 second-innings rows in audit corpus |
| 7 | Match 48610 | Remove the 93 chase rows from the scoring corpus | PASS | 101 retained rows |
| 8 | Match 48610 | Excluded chase contains zero `other` extras | PASS | 0 `other` rows |
| 9 | Match 48610 | Excluded chase contributes 11 pressure boundaries | PASS | 11 boundary rows; 9 fours + 2 sixes |
| 10 | `other` extras | `other` count is unchanged by the chase exclusion | PASS | audit=256; scoring=256 |
| 11 | Q10 boundaries | Audit boundary-conceded counts | PASS | legal only=9,767, legal + overstep=9,801, legal + overstep + other=9,827 |
| 12 | Q10 boundaries | Audit weighted boundary numerators | PASS | legal only=6552.537349, legal + overstep=6576.615108, legal + overstep + other=6594.333604 |
| 13 | Q10 boundaries | Audit weighted boundary denominator | PASS | 30057.770551 observed / 30057.770551 approved |
| 14 | Q10 boundaries | Scoring boundary-conceded counts | PASS | legal only=9,756, legal + overstep=9,790, legal + overstep + other=9,816 |
| 15 | Q10 boundaries | Scoring weighted boundary numerators | PASS | legal only=6547.268516, legal + overstep=6571.346275, legal + overstep + other=6589.064771 |
| 16 | Q10 boundaries | Scoring weighted boundary denominator | PASS | 30021.669303 observed / 30021.669303 approved |
| 17 | `other` extras | Pressure-set `other` contents | PASS | rows=88, batter_runs=139, extras_runs=104, boundaries=26, weighted_extras=74.467115, weighted_batter_runs=96.670587 |
| 18 | Pressure engine | Eight canonical scenarios reproduce approved P_bat/P_bowl | PASS | max |delta|=0.0498; tolerance 0.1 |
| 19 | Pressure engine | Scoring-corpus P_bat matches independent recomputation | PASS | max |diff|=2.84e-14 |
| 20 | Pressure engine | Scoring-corpus P_bowl matches independent recomputation | PASS | max |diff|=0 |
| 21 | Pressure engine | Scoring-corpus pressure values are finite | PASS | 0 non-finite P_bat; 0 non-finite P_bowl |
| 22 | Pressure engine | Pressure values lie in [0, 100] | PASS | P_bat [0.1575, 99.9999]; P_bowl [1.4774, 98.4804] |
| 23 | Pressure engine | Pressure weights use the approved square above 60 | PASS | max |diff| w_bat=0; w_bowl=0 |
| 24 | Pressure engine | Audit-corpus P1 fallback matches independent recomputation | PASS | max |diff| P_bat=2.84e-14; P_bowl=0 |
| 25 | Delivery attribution | Ball-faced, legal, dot, boundary, dismissal and bowler-run attribution | PASS | 191,963 deliveries checked |
| 26 | Delivery attribution | `other` remains provisional no-ball-like | PASS | 256 `other` rows; BF=1; legal=0; dot=0; bowler runs=batter+extras |
| 27 | Delivery attribution | Retire Out is excluded from the batter dismissal numerator | PASS | 6 Retire Out rows |
| 28 | Reference moments | Batter reference moments match independent recomputation | PASS | 10 format-metric moments checked |
| 29 | Reference moments | Bowler reference moments match independent recomputation | PASS | 10 format-metric moments checked |
| 30 | Peer means | Approved peer means match independent recomputation | PASS | 12 peer means checked |
| 31 | Composite | Batter shrinkage, z-scores and weighted composite | PASS | 907 format records checked |
| 32 | Format eligibility | Batter N_raw and N_eff,del gate | PASS | 243 records pass the format gate |
| 33 | Format eligibility | Batter baseline exposure gate | PASS | 238 records pass the baseline gate |
| 34 | Format eligibility | Batter all five metric denominators are positive | PASS | 906 records pass the denominator gate |
| 35 | Format eligibility | Batter composite-ready definition | PASS | 144 composite-ready records |
| 36 | Composite | Bowler shrinkage, z-scores and weighted composite | PASS | 628 format records checked |
| 37 | Format eligibility | Bowler N_raw and N_eff,del gate | PASS | 224 records pass the format gate |
| 38 | Format eligibility | Bowler baseline exposure gate | PASS | 306 records pass the baseline gate |
| 39 | Format eligibility | Bowler all five metric denominators are positive | PASS | 628 records pass the denominator gate |
| 40 | Format eligibility | Bowler composite-ready definition | PASS | 209 composite-ready records |
| 41 | Independent aggregation | Batter: engine record table matches independent aggregation | PASS | 907 records compared |
| 42 | Independent aggregation | Bowler: engine record table matches independent aggregation | PASS | 628 records compared |
| 43 | Player aggregation | Batter equal-weight format composite and eligibility | PASS | 746 player rows checked |
| 44 | Player aggregation | Batter F format labels and ordering | PASS | all F labels match |
| 45 | Calibration | Batter calibration population size | PASS | n=122 / approved 122 |
| 46 | Calibration | Batter calibration mean and population SD | PASS | mu=0.1036068081 (approved 0.1036068081); sigma=0.6610638828 (approved 0.6610638828) |
| 47 | Reliability | Batter Z_std and reliability formula | PASS | max |diff| Z_std=0; Reliability=0 |
| 48 | Reliability | Batter reliability is finite and in [0, 100] | PASS | range [9.119847, 85.169842] |
| 49 | Ranking | Batter deterministic order and contiguous ranks | PASS | 101 ranked players; order_ok=True; ranks_ok=True |
| 50 | Ranking | Batter no player with M_role < 10 is ranked | PASS | 0 violations |
| 51 | Ranking | Batter ranked scores are finite and non-missing | PASS | 0 non-finite Z_comp |
| 52 | Ranking | Batter player IDs are unique | PASS | 0 duplicate player rows |
| 53 | Ranking | Batter ranked player names are present | PASS | 0 missing names |
| 54 | Top 10 | Batter top 10 matches the full ranking table | PASS | 10 rows; IDs=3374,4369,6288,37052,2485,2930,1699,2921,4246,6651 |
| 55 | Player aggregation | Bowler equal-weight format composite and eligibility | PASS | 507 player rows checked |
| 56 | Player aggregation | Bowler F format labels and ordering | PASS | all F labels match |
| 57 | Calibration | Bowler calibration population size | PASS | n=173 / approved 173 |
| 58 | Calibration | Bowler calibration mean and population SD | PASS | mu=0.0256919706 (approved 0.0256919707); sigma=0.6655792246 (approved 0.6655792246) |
| 59 | Reliability | Bowler Z_std and reliability formula | PASS | max |diff| Z_std=0; Reliability=0 |
| 60 | Reliability | Bowler reliability is finite and in [0, 100] | PASS | range [11.471032, 87.822761] |
| 61 | Ranking | Bowler deterministic order and contiguous ranks | PASS | 141 ranked players; order_ok=True; ranks_ok=True |
| 62 | Ranking | Bowler no player with M_role < 10 is ranked | PASS | 0 violations |
| 63 | Ranking | Bowler ranked scores are finite and non-missing | PASS | 0 non-finite Z_comp |
| 64 | Ranking | Bowler player IDs are unique | PASS | 0 duplicate player rows |
| 65 | Ranking | Bowler ranked player names are present | PASS | 0 missing names |
| 66 | Top 10 | Bowler top 10 matches the full ranking table | PASS | 10 rows; IDs=4658,4840,7364,7690,781,7699,1596,7503,6643,8661 |
| 67 | Populations | Batter approved population counts | PASS | composite_records=144, composite_players=122, final_records=123, final_players=101, m_lt_10=21, m_all_ge_10=103, calibration=122 |
| 68 | Populations | Bowler approved population counts | PASS | composite_records=209, composite_players=173, final_records=177, final_players=141, m_lt_10=32, m_all_ge_10=146, calibration=173 |
| 69 | Populations | Both-role final-eligible players | PASS | 23 players |
| 70 | Output files | All required Stage 5 CSV outputs exist, are non-empty and have expected row counts | PASS | 9 CSV files checked |

## 8. Remaining limitations

- The `other` extra classification remains unresolved.  The primary bowler boundary-conceded treatment is the provisional all-extras rule (`PROVISIONAL_OTHER`), not a fully verified classification.
- Correlation pair identities remain unresolved and were not used to alter the approved equal-weight composite.
- Match 48610's DLS provenance remains unresolved; the treatment is resolved by excluding the chase.  The \(P_1\) fallback is an audit/sensitivity device only.
- The Retire Out exclusion is documented as proposed and is not fully source-verified across every scorecard.
- The optional capped-\(N_{eff}\) sensitivity was not run; no numeric \(C\) is registered.  It is not a primary blocker.

## 9. Acceptance statement

All critical checks pass.  The Stage 5 primary scoring outputs agree with the approved Stage 4.2 methodology and the approved corpus treatment.  This report does not convert any unresolved limitation above into a verified fact.
