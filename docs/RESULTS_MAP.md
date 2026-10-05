# Results map

Each claim the paper makes is listed below with the number that supports it and the output that contains it. The claims are written to stay within what the design identifies. All effects are percent changes in residential price unless stated otherwise.

## A. Identified bounds (core claims)

| # | Claim | Numbers | Output |
|---|---|---|---|
| A1 | No rollback produced a detectable price reduction. | OH −1.8% (p 0.68), KS +0.9% (0.88), MT −3.6% (0.28); bills −0.7%, +1.1%, +2.1% | T2_main_estimates, Fig1 |
| A2 | Savings larger than about 10% are ruled out in the three causal episodes (Ohio's permutation bound ranges 8.7–12.4% across windows). | one-sided normal bounds 7.4 / 5.4 / 8.9% (two-sided 95% CI lower ends 8.5 / 6.5 / 9.9%); rank-based bounds 10.2 / 8.2 / 10.4% (OH/KS/MT); pooled −1.5% [−7.4, +4.8] | T2_main_estimates, R3_benchmark_tests, R4_ohio_windows, R5_pooled |
| A3 | For Ohio's obligated (IOU and supplier) customers, savings above about 16% are ruled out. | obligated-only −3.2% [−15.6, +11.0] | U3_obligated_only |
| A4 | Ohio's estimate is the effect of the SB 310 / HB 6 package, not of the RPS cut alone. | SB 310 froze efficiency requirements for 2015–16 and removed the in-state renewable requirement; HB 6 ended efficiency mandates and added nuclear/coal charges | manuscript Section 2.2; R7_ohio_breakdown |
| A4b | The other measures in the Ohio package were of similar or larger size than the RPS change and moved bills in both directions. | 2019 statewide costs: efficiency programs 2.1% of retail revenue, RPS 0.5%; OVEC rider up to $1.50/month (1.1% of the 2024 bill); nuclear charge blocked before collection | C4_ohio_package (Table S12) |
| A4c | The known bill-raising measures in the Ohio package cannot overturn the 11.5% rejection. | offset absorbed: 4.5 pp (normal), 1.4 pp (permutation); OVEC + solar caps ≤ 1.2% of the 2024 bill; 8.1% not robust (0.8 pp normal; not rejected by permutation) | R7_ohio_breakdown (Table S7b), C4_ohio_package |
| A5 | The design cannot detect accounting-scale effects. | 2×SE 7.1–8.1%; MDE at 80% power 10.1–11.6% | T2_main_estimates, C3_accounting_tests |

## B. The cost scale (measured facts, not causal estimates)

| # | Claim | Numbers | Output |
|---|---|---|---|
| B1 | Ohio's RPS compliance cost was about half a percent of bills when it was frozen. | 0.53% of average retail bill in 2013; 0.34–0.79% over 2014–24 | C1, C2 |
| B2 | Direct savings available from Ohio's freeze and cut were about 0.3% of bills. | cost per pp × requirement cut, mean 2014–24 = 0.28% (0.37% in 2024) | C2_ohio_accounting |
| B3 | The adoption-side estimates imply savings roughly 25–40 times larger. | G&N horizon-matched 7.0%, scaled 8.1–11.5% (reversal X/(1+X), averaged in log points) | C3, R2_benchmarks |
| B4 | About 15% of Ohio residential load (municipals and co-ops) was never covered. | obligated share 0.85 (OH), 0.69 (KS), 0.52 (MT), 0.99 (WV) | U1_coverage |

## C. Benchmark tests (what is and is not rejected)

Note: the national accounting benchmark is LBNL 2026 (~5%), and every test is reported under the normal approximation and the placebo rank. Adoption benchmarks are reversed as X/(1+X) and averaged in log points (code/rpsrb/bench.py). Under the rank test only Ohio's 11.5% benchmark is rejected (p 0.04, also with any one donor dropped: R9_ohio_rank_loo); 7.0% (p 0.12) and 8.1% (p 0.08) are not; 5% is rejected nowhere. Rows C1–C6 below give the normal-approximation results; see R3/R4/U2/U3 for the `prank_*` columns.

| # | Claim | Numbers | Output |
|---|---|---|---|
| C1 | Over the full window, the normal approximation rejects the scaled Ohio benchmarks but not the horizon-matched one. | horizon-matched −7.0%, p 0.066; scaled −8.1 / −11.5%, p 0.031 / 0.002 | R3_benchmark_tests |
| C2 | The permutation rejection depends on including 2024. | windows ending 2018 and 2020–2023: rank p ≥ 0.08 for every benchmark; normal p for scaled-high 0.008–0.04 | R4_ohio_windows, Fig2 |
| C3 | After adjusting for coverage, or using obligated customers only, the rejections weaken. | coverage-adjusted (normal / rank): scaled-low 0.07 / 0.12, scaled-high 0.009 / 0.08; obligated-only scaled-high 0.10 / 0.04 | U2, U3 |
| C4 | Kansas and Montana are not tests of symmetry, because their standards did not bind and the predicted effect is zero. | equivalence margins 7.6% (KS), 8.9% (MT); OH 7.4% | R3_benchmark_tests |
| C5 | Montana's four post years cannot test the 11–17% claim. | horizon-matched benchmark −2.2%, p 0.66 / 0.60 | R2, R3 |
| C6 | Under permutation inference, savings of the size of LBNL's national average compliance cost (~5%) are rejected nowhere (normal approximation rejects only Kansas with a 2016 start or Kansas bills, R8). | p (normal / rank): OH 0.18 / 0.20, KS 0.06 / 0.12, MT 0.33 / 0.36, pooled 0.13 / 0.16 | R3, R5 |

## D. Non-binding repeals

| # | Claim | Numbers | Output |
|---|---|---|---|
| D1 | Repealing non-binding standards did not reduce renewable generation. | KS renewable share +8.3 pp (p 0.16); MT +1.5 pp (0.44) | T3_timing_composition |
| D2 | Prices did not move in either direction beyond ±7–10%. | KS 90% CI [−5.4, +7.6]; MT [−8.9, +2.1] | R3_benchmark_tests |

## E. Ohio dynamics and mechanisms (suggestive only)

| # | Claim | Numbers | Output |
|---|---|---|---|
| E1 | Ohio prices ran below the counterfactual in 2016–21 and above it in 2023–24. | annual effects −2.7 to −6.2% (2016–21), +3.4 / +5.0% (2023–24) | R1_annual_effects, Fig2 |
| E2 | The obligated-minus-exempt gap fell by about 9% (p 0.10). About a third of that is exempt-side prices rising. | within −9.2%; obligated −4.3%; exempt +3.0% (20 donors) | U5_ohio_decomposition, Fig3 |
| E3 | Gas generation share rose relative to the counterfactual (association; shale geography confounds it). | +13.3 pp (p 0.04) | T3 |
| E4 | Fuel pass-through explains the 2022 change; auction timing coincides with 2023. | cumulative 0.32 [0.22, 0.43]; 2022 obs/pred +2.1/+2.0 | S6_passthrough |

## F. Robustness and diagnostics

| # | Item | Numbers | Output |
|---|---|---|---|
| F1 | Leave-one-out donor ranges | OH [−2.1, −1.4], KS [+0.5, +1.9], MT [−3.8, −3.2] | S2_robustness |
| F2 | Dropping donors with terminal-year targets; dropping TX (repealed 2023) | OH −1.2%, KS +1.8%, MT −3.2%; drop TX −1.7%, +0.5%, −3.7% | R6_donor_exclusions |
| F3 | A uniform fit rule flags West Virginia (price) and Kansas and West Virginia (bills). | WV price pre-MSPE 3.9× donor median; KS bill 2.3×, WV bill 3.4× | S3_weights_fit |
| F4 | In-time placebos (onset 2004, window to 2007); own-state adoption-period runs | placebo OH −0.8%, KS −5.2%, WV −6.8%, MT −1.7%; own-state OH +2.3%, KS +5.6%, WV +10.2%, MT +1.0% | S2_robustness |
| F5 | Conformal p under three statistics; classic synthetic control | see S2; SC OH −1.0%, KS +2.0%, MT −2.6% | S2_robustness |

## G. What does not work (report as a limitation, or omit)

| # | Item | Numbers | Output |
|---|---|---|---|
| G1 | An adoption-side within-state design fails pre-trends. | gap rises 7–8% in the 3–6 years before adoption; post SEs 3–5 pp | A1, A2, FigS3 |
| G2 | Irreversibility is not identified. | zero and partial reversal cannot be distinguished (C2, C3) | n/a |
| G3 | West Virginia +13.4% is not causal. | fails pre-fit; RMSPE-ratio p 0.12; not an RPS state per LBNL | S3 |
