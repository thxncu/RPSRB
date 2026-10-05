"""40 - Check reproduced numbers against the values printed in the manuscript and supplementary material
("Does repealing renewable portfolio standards lower electricity prices? Evidence and bounds from four
U.S. rollbacks"). Writes output/tables/Z_manuscript_check.csv and prints any mismatch.

Tolerance: 0.051 for values printed to one decimal, 0.0051 for two-decimal p-values.
"""
import numpy as np
import pandas as pd

from rpsrb.config import TAB

r = lambda f: pd.read_csv(TAB / f"{f}.csv")
t2 = r("T2_main_estimates").set_index(["outcome", "state"])
r3 = r("R3_benchmark_tests").set_index("state")
r5 = r("R5_pooled").iloc[0]
u2 = r("U2_coverage_adjusted").set_index("state")
u3 = r("U3_obligated_only").set_index(["state", "window"])
u5 = r("U5_ohio_decomposition").groupby("series")[["avg_2014_24_pct", "p_avg"]].first()
s2 = r("S2_robustness").set_index(["check", "state"])
s3 = r("S3_weights_fit").set_index("state")
s4 = r("S4_burden").set_index(["income", "state"])
t3 = r("T3_timing_composition").set_index("state")
r8 = r("R8_kansas_onset").set_index(["outcome", "onset"])
c2 = r("C2_ohio_accounting")
C = []


def chk(label, got, want, tol=0.051):
    C.append({"item": label, "manuscript": want, "reproduced": round(float(got), 4), "match": abs(got - want) <= tol})


# Table 3 (main estimates)
for (o, s), (e, lo, hi, p) in {("price", "OH"): (-1.8, -8.5, 5.4, .68), ("price", "KS"): (.9, -6.5, 8.9, .88),
                               ("price", "MT"): (-3.6, -9.9, 3.2, .28), ("price", "WV"): (13.4, 5.1, 22.5, .04),
                               ("bill", "OH"): (-.7, -6.8, 5.8, .92), ("bill", "KS"): (1.1, -5.8, 8.6, .88),
                               ("bill", "MT"): (2.1, -4.6, 9.3, .64), ("bill", "WV"): (11.9, 4.2, 20.2, .04)}.items():
    x = t2.loc[(o, s)]
    chk(f"Table 3 {o} {s} effect", x.effect_pct, e)
    chk(f"Table 3 {o} {s} CI low", x.ci95_lo_pct, lo)
    chk(f"Table 3 {o} {s} CI high", x.ci95_hi_pct, hi)
    chk(f"Table 3 {o} {s} p", x.p_placebo, p, .0051)
for s in ["OH", "KS", "MT"]:   # Table 3 note: 80%-power MDE (2.8 x SE) about 10-12%
    m = t2.loc[("price", s), "mde80_2.8se_pct"]
    chk(f"Table 3 note MDE80 {s} in 10-12%", float(10 <= round(m) <= 12), 1.0, 0)
chk("Pooled OH/KS/MT effect", r5.effect_pct, -1.5)
chk("Pooled OH/KS/MT p", r5.p_placebo, .76, .0051)
# Section 4.1 one-sided bounds
for s, (n, k) in {"OH": (-7.4, -10.2), "KS": (-5.4, -8.2), "MT": (-8.9, -10.4)}.items():
    chk(f"4.1 one-sided normal bound {s}", r3.loc[s, "normal_lower_bound95_pct"], n)
    chk(f"4.1 permutation bound {s}", r3.loc[s, "rank_lower_bound_pct"], k)
# Table 2 benchmarks (reversal X/(1+X), log-point averages)
r2 = r("R2_benchmarks").set_index("state")
for s, k, v in [("OH", "gn_horizon_matched", -7.0), ("OH", "gn_scaled_low", -8.1), ("OH", "gn_scaled_high", -11.5),
                ("KS", "gn_horizon_matched", -6.4), ("MT", "gn_horizon_matched", -2.2)]:
    chk(f"Table 2 {s} {k}", r2.loc[s, k], v)
# Table 4 (benchmark tests; normal / rank)
T4 = {"OH": {"lbnl_avg": (.18, .20), "gn_horizon_matched": (.07, .12), "gn_scaled_low": (.03, .08), "gn_scaled_high": (.002, .04)},
      "KS": {"lbnl_avg": (.06, .12), "gn_horizon_matched": (.03, .08)},
      "MT": {"lbnl_avg": (.33, .36), "gn_horizon_matched": (.66, .60)}}
for s, d in T4.items():
    chk(f"Table 4 {s} margin", r3.loc[s, "tost_smallest_equivalence_margin_pct"], {"OH": 7.4, "KS": 7.6, "MT": 8.9}[s])
    for k, (pn, pr) in d.items():
        chk(f"Table 4 {s} {k} normal p", r3.loc[s, f"p_{k}"], pn, .0051 if pn >= .01 else .0006)
        chk(f"Table 4 {s} {k} rank p", r3.loc[s, f"prank_{k}"], pr, .0051)
o = u3.loc[("OH", "2014-2024")]
chk("Obligated-only OH effect", o.effect_pct, -3.2)
for k, (pn, pr) in {"gn_horizon_matched": (.29, .25), "gn_scaled_low": (.23, .21), "gn_scaled_high": (.10, .04)}.items():
    chk(f"Obligated-only {k} normal p", o[f"p_{k}"], pn, .0051)
    chk(f"Obligated-only {k} rank p", o[f"prank_{k}"], pr, .0051)
for k, (pn, pr) in {"gn_scaled_low": (.07, .12), "gn_scaled_high": (.009, .08)}.items():
    chk(f"Coverage-adjusted {k} normal p", u2.loc["OH", f"p_{k}"], pn, .0051 if pn >= .01 else .0006)
    chk(f"Coverage-adjusted {k} rank p", u2.loc["OH", f"prank_{k}"], pr, .0051)
# Ohio windows (S7a): permutation bounds and rejections
r4 = r("R4_ohio_windows").set_index("window")
for w, v in {"2014-2018": -8.7, "2014-2020": -11.9, "2014-2021": -12.4, "2014-2024": -10.2}.items():
    chk(f"S7a rank bound {w}", r4.loc[w, "rank_lower_bound_pct"], v)
for w in ["2014-2018", "2014-2020", "2014-2021", "2014-2022", "2014-2023"]:
    chk(f"S7a {w} min rank p >= 0.08", float(r4.loc[w, [c for c in r4 if c.startswith("prank_")]].min() >= .08 - 1e-9), 1.0, 0)
    chk(f"S7a {w} normal p scaled-high in 0.008-0.04", float(.0075 <= r4.loc[w, "p_gn_scaled_high"] < .045), 1.0, 0)
chk("S7a bound range min (2014-2018)", r4.rank_lower_bound_pct.max(), -8.7)
chk("S7a bound range max (2014-2021)", r4.rank_lower_bound_pct.min(), -12.4)
# S7c leave-one-donor-out
r9 = r("R9_ohio_rank_loo")
chk("S7c every LOO rank p for scaled-high <= 0.05", float((r9.prank_gn_scaled_high <= .05).all()), 1.0, 0)
# Kansas 2016 and bills vs 5% (normal)
chk("S11 KS 2016 price p 5% normal", r8.loc[("price", 2016), "p_lbnl_avg"], .02, .0051)
chk("S11 KS bill 2015 p 5% normal", r8.loc[("bill", 2015), "p_lbnl_avg"], .04, .0051)
chk("S11 KS bill 2016 p 5% normal", r8.loc[("bill", 2016), "p_lbnl_avg"], .04, .0051)
# Fig. 3 decomposition
for k, (e, p) in {"state_average": (-1.8, .67), "obligated": (-4.3, .38), "exempt": (3.0, .52),
                  "within_difference": (-9.2, .10)}.items():
    chk(f"Fig. 3 {k} effect", u5.loc[k, "avg_2014_24_pct"], e)
    chk(f"Fig. 3 {k} p", u5.loc[k, "p_avg"], p, .0051)
# Kansas 2016 start
chk("Kansas 2016 price effect", r8.loc[("price", 2016), "effect_pct"], 1.4)
from rpsrb.bench import benchmarks
chk("Kansas 2016 horizon-matched benchmark", benchmarks("KS", 2016)["gn_horizon_matched"], -5.7)
# Accounting benchmark
chk("Ohio accounting saving 2014-24 mean", c2.implied_saving_pct.mean(), .28, .0051)
chk("Ohio accounting saving 2024", c2.set_index("year").implied_saving_pct.loc[2024], .37, .0051)
# Supplementary S2-S6 selections
for (k, s), v in {("Never-RPS donors only (%)", "OH"): -.9, ("Voluntary-goal donors only (%)", "OH"): -5.6,
                  ("Difference-in-differences, donor mean (%)", "KS"): 8.0,
                  ("Difference-in-differences, donor mean (%)", "OH"): -.4,
                  ("Difference-in-differences, donor mean (%)", "MT"): -3.7,
                  ("Synthetic control (classic), mean post gap (%)", "OH"): -1.0,
                  ("Synthetic control (classic), mean post gap (%)", "KS"): 2.0,
                  ("Synthetic control (classic), mean post gap (%)", "MT"): -2.6,
                  ("Own-state adoption period, onset 2008, window to 2013 (%)", "OH"): 2.3,
                  ("Own-state adoption period, onset 2009, window to 2014 (%)", "KS"): 5.6,
                  ("Own-state adoption period, onset 2009, window to 2014 (%)", "WV"): 10.2,
                  ("Own-state adoption period, onset 2015, window to 2020 (%)", "MT"): 1.0,
                  ("In-time placebo, onset 2004, window to 2007 (%)", "OH"): -.8,
                  ("In-time placebo, onset 2004, window to 2007 (%)", "KS"): -5.2,
                  ("In-time placebo, onset 2004, window to 2007 (%)", "WV"): -6.8,
                  ("In-time placebo, onset 2004, window to 2007 (%)", "MT"): -1.7,
                  ("Excluding TX (%)", "OH"): -1.7, ("Excluding TX (%)", "KS"): .5, ("Excluding TX (%)", "MT"): -3.7,
                  ("Industrial price, descriptive (%)", "MT"): 18.6,
                  ("Residential use per customer (%)", "MT"): 3.1}.items():
    chk(f"S2 {k} {s}", s2.loc[(k, s), "value"], v)
for s, v in {"OH": .96, "KS": .60, "MT": .60}.items():
    chk(f"S2 conformal |mean| {s}", s2.loc[("Conformal p (abs_mean)", s), "value"], v, .0051)
for s, v in {"OH": 2.07, "KS": 2.28, "WV": 4.65, "MT": 2.26}.items():
    chk(f"S3 pre-RMSPE {s}", s3.loc[s, "pre_rmspe_pct"], v, .0051)
for s, v in {"KS": 2.28, "WV": 3.36}.items():
    chk(f"S3 bill pre-MSPE/median {s}", s3.loc[s, "bill_pre_mspe_over_median"], v, .0051)
for s, v in {"OH": -5.1, "KS": -3.3, "MT": -3.2}.items():
    chk(f"S4 burden {s}", s4.loc[("baseline", s), "effect_pct"], v)
for s, (re_, gas) in {"OH": (-1.3, 13.3), "KS": (8.3, -5.1), "MT": (1.5, -.4)}.items():
    chk(f"S5a RE share {s}", t3.loc[s, "re_share_pp"], re_)
    chk(f"S5a gas share {s}", t3.loc[s, "gas_share_pp"], gas)

c4 = r("C4_ohio_package").set_index("component")
chk("4.3 efficiency cost share of retail revenue 2019", c4.loc["Energy-efficiency and peak-demand riders", "share_of_retail_revenue_pct"], 2.1)
chk("4.3 RPS cost share of retail revenue 2019", c4.loc["RPS (alternative energy) riders", "share_of_retail_revenue_pct"], .5)
chk("4.3 OVEC cap share of 2024 bill (about 1%)", c4.loc["Legacy generation (OVEC coal) rider", "res_high_pct_of_avg_bill"], 1.1)
r7 = r("R7_ohio_breakdown").set_index(["obligated_coverage", "elasticity"])
chk("4.3 offset 11.5% normal", r7.loc[(1.0, "high (5.0%/pp)"), "max_rider_offset_pp_still_rejecting"], 4.5)
chk("4.3 offset 11.5% rank", r7.loc[(1.0, "high (5.0%/pp)"), "max_rider_offset_pp_still_rejecting_rank"], 1.4)
chk("4.3 offset 8.1% normal", r7.loc[(1.0, "low (3.4%/pp)"), "max_rider_offset_pp_still_rejecting"], .8)
chk("4.3 8.1% rank not rejected without offset", float(r7.loc[(1.0, "low (3.4%/pp)"), "max_rider_offset_pp_still_rejecting_rank"] < 0), 1.0, 0)
chk("4.3 OVEC + solar caps below rank margin", float(c4.loc["Legacy generation (OVEC coal) rider", "res_high_pct_of_avg_bill"] + c4.loc["Solar generation charge (cap)", "res_high_pct_of_avg_bill"] < r7.loc[(1.0, "high (5.0%/pp)"), "max_rider_offset_pp_still_rejecting_rank"]), 1.0, 0)
Z = pd.DataFrame(C)
Z.to_csv(TAB / "Z_manuscript_check.csv", index=False)
print(f"{Z.match.sum()} of {len(Z)} manuscript values reproduced")
if (~Z.match).any():
    print(Z[~Z.match].to_string(index=False))
