"""20 - Bounds and benchmark tests at the state level.

Tables
  R1_annual_effects        annual SDID effects (lambda-adjusted gaps) with year-specific donor placebo bands
  R2_benchmarks            symmetric-reversal benchmarks: Greenstone-Nath path matched to each post-horizon;
                           for Ohio also scaled by the requirement cut vs the original SB 221 schedule
  R3_benchmark_tests       one-sided tests (H0: savings at least as large as benchmark), 90% CI, TOST margin
  R4_ohio_windows          same tests with Ohio post window ending 2018, 2020, 2021, 2024
  R5_pooled                pooled OH/KS/MT estimate with joint donor placebo distribution
  R6_donor_exclusions      dropping donors with terminal-year targets
  R7_ohio_breakdown        how much obligated-load coverage / HB 6 rider offset the Ohio rejection tolerates
"""
import numpy as np
import pandas as pd
from scipy.stats import norm

from rpsrb.config import (TREATED, CAUSAL, DONOR_LIST, EXPIRING, OH_CUT, GN_PATH, GN_PER_PP,
                          LBNL_AVG)
from rpsrb.sdid import run_case, pct
from rpsrb.data import wide, save

LOGP = wide("residential_price")
from rpsrb.bench import benchmarks, one_sided_p, rank_p, lp, gn_log, rev_pct, scaled_log, scale_pct


cases = {s: run_case(LOGP, s, t, DONOR_LIST, keep_paths=True) for s, t in TREATED.items()}

# ------------------------------------------------------------------ annual effects
rows = []
for s, r in cases.items():
    P = np.array([pf["annual"] for pf in r["placebo_fits"].values()])
    for k, y in enumerate(r["years"]):
        if y < TREATED[s] - 6:
            continue
        sd = P[:, k].std(ddof=1)
        rows.append({"state": s, "year": y, "event_time": y - TREATED[s], "effect_pct": pct(r["annual"][k]),
                     "band95_lo_pct": pct(-1.96 * sd), "band95_hi_pct": pct(1.96 * sd),
                     "p_year": (1 + np.sum(np.abs(P[:, k]) >= abs(r["annual"][k]))) / (1 + len(P)),
                     "gn_reversal_pct": rev_pct(gn_log(y - TREATED[s])) if y >= TREATED[s] else np.nan,
                     "gn_scaled_low_pct": rev_pct(scaled_log(GN_PER_PP[0], y)) if s == "OH" and y in OH_CUT else np.nan,
                     "gn_scaled_high_pct": rev_pct(scaled_log(GN_PER_PP[1], y)) if s == "OH" and y in OH_CUT else np.nan})
save(pd.DataFrame(rows), "R1_annual_effects")

# ------------------------------------------------------------------ benchmarks and tests
brows, trows = [], []
for s, r in cases.items():
    B = benchmarks(s, TREATED[s])
    brows.append({"state": s, "post_years": r["T1"], **B})
    tau, se = r["tau"], r["se"]
    row = {"state": s, "effect_pct": r["pct"], "ci90_lo_pct": pct(tau - 1.645 * se),
           "ci90_hi_pct": pct(tau + 1.645 * se),
           "tost_smallest_equivalence_margin_pct": max(abs(pct(tau - 1.645 * se)), abs(pct(tau + 1.645 * se))),
           # largest saving NOT rejected by the one-sided placebo-rank test at 5% (24 placebos: rejects only
           # when every shifted placebo falls below tau), i.e. lower bound = tau - max(placebo)
           "rank_lower_bound_pct": pct(tau - np.max(r["placebos"].values)),
           "normal_lower_bound95_pct": pct(tau - 1.645 * se)}
    for k, v in B.items():
        row[f"p_{k}"] = one_sided_p(tau, se, v)
        row[f"prank_{k}"] = rank_p(tau, r["placebos"], v)
    trows.append(row)
save(pd.DataFrame(brows), "R2_benchmarks")
R3 = save(pd.DataFrame(trows), "R3_benchmark_tests")
print(R3.round(3).to_string(index=False))

rows = []
for end in [2018, 2020, 2021, 2022, 2023, 2024]:
    r = run_case(LOGP, "OH", 2014, DONOR_LIST, end=end)
    B = benchmarks("OH", 2014, end)
    rows.append({"window": f"2014-{end}", "effect_pct": r["pct"], "placebo_se": r["se"], "p_placebo": r["p"],
                 "ci95_lo_pct": r["ci_lo"], "ci95_hi_pct": r["ci_hi"],
                 "normal_lower_bound95_pct": pct(r["tau"] - 1.645 * r["se"]),
                 "rank_lower_bound_pct": pct(r["tau"] - np.max(r["placebos"].values)),
                 **{f"bench_{k}": v for k, v in B.items()},
                 **{f"p_{k}": one_sided_p(r["tau"], r["se"], v) for k, v in B.items()},
                 **{f"prank_{k}": rank_p(r["tau"], r["placebos"], v) for k, v in B.items()}})
save(pd.DataFrame(rows), "R4_ohio_windows")

# ------------------------------------------------------------------ pooled with joint placebo
pooled = np.mean([cases[s]["tau"] for s in CAUSAL])
plac = np.array([np.mean([cases[s]["placebos"][d] for s in CAUSAL]) for d in DONOR_LIST])
se_p = plac.std(ddof=1)
save(pd.DataFrame([{"set": "OH, KS, MT", "effect_pct": pct(pooled), "placebo_se": se_p,
                    "p_placebo": (1 + np.sum(np.abs(plac) >= abs(pooled))) / (1 + len(plac)),
                    "ci95_lo_pct": pct(pooled - 1.96 * se_p), "ci95_hi_pct": pct(pooled + 1.96 * se_p),
                    "ci90_lo_pct": pct(pooled - 1.645 * se_p), "ci90_hi_pct": pct(pooled + 1.645 * se_p),
                    "p_lbnl_avg": one_sided_p(pooled, se_p, -LBNL_AVG),
                    "prank_lbnl_avg": rank_p(pooled, plac, -LBNL_AVG)}]), "R5_pooled")

# ------------------------------------------------------------------ donor exclusions
rows = []
for lab, dl in [("baseline (24)", DONOR_LIST),
                ("drop terminal-year targets PA MO WI OK ND SD (18)", [d for d in DONOR_LIST if d not in EXPIRING]),
                ("drop PA MO WI AZ (20)", [d for d in DONOR_LIST if d not in {"PA", "MO", "WI", "AZ"}]),
                ("drop TX (23)", [d for d in DONOR_LIST if d != "TX"])]:
    for s, t in TREATED.items():
        r = run_case(LOGP, s, t, dl)
        rows.append({"donor_set": lab, "state": s, "effect_pct": r["pct"], "p_placebo": r["p"],
                     "ci95_lo_pct": r["ci_lo"], "ci95_hi_pct": r["ci_hi"]})
save(pd.DataFrame(rows), "R6_donor_exclusions")

# ------------------------------------------------------------------ Ohio breakdown
tau, se = cases["OH"]["tau"], cases["OH"]["se"]
BO = benchmarks("OH", 2014)
rows = []
for cov in [1.0, 0.9, 0.848, 0.8, 0.7]:
    for lab, k in [("low (3.4%/pp)", "gn_scaled_low"), ("high (5.0%/pp)", "gn_scaled_high")]:
        B = scale_pct(BO[k], cov)
        thr = lp(B) + 1.645 * se
        rows.append({"obligated_coverage": cov, "elasticity": lab, "benchmark_pct": B,
                     "p_one_sided": one_sided_p(tau, se, B),
                     "max_rider_offset_pp_still_rejecting": 100 * (tau - thr),
                     "max_rider_offset_pp_still_rejecting_rank":
                         100 * (tau - lp(B) - cases["OH"]["placebos"].max())})
save(pd.DataFrame(rows), "R7_ohio_breakdown")
# ------------------------------------------------------------------ Kansas onset 2016 (SB 91 effective 1 Jan 2016)
rows = []
for lab, M in [("price", LOGP), ("bill", wide("residential_bill"))]:
    for onset in [2015, 2016]:
        r = run_case(M, "KS", onset, DONOR_LIST)
        B = benchmarks("KS", onset)
        rows.append({"outcome": lab, "onset": onset, "effect_pct": r["pct"], "p_placebo": r["p"],
                     "ci95_lo_pct": r["ci_lo"], "ci95_hi_pct": r["ci_hi"],
                     **{f"p_{k}": one_sided_p(r["tau"], r["se"], v) for k, v in B.items()},
                     **{f"prank_{k}": rank_p(r["tau"], r["placebos"], v) for k, v in B.items()}})
save(pd.DataFrame(rows), "R8_kansas_onset")

# ------------------------------------------------------------------ leave-one-donor-out for the permutation rejection
# With 23 placebos the smallest attainable rank p is 1/24 = 0.042.
BO = benchmarks("OH", 2014)
rows = []
for d in DONOR_LIST:
    dl = [x for x in DONOR_LIST if x != d]
    r = run_case(LOGP, "OH", 2014, dl)
    rows.append({"dropped": d, "effect_pct": r["pct"],
                 **{f"prank_{k}": rank_p(r["tau"], r["placebos"], v) for k, v in BO.items()},
                 **{f"p_{k}": one_sided_p(r["tau"], r["se"], v) for k, v in BO.items()}})
save(pd.DataFrame(rows), "R9_ohio_rank_loo")
print("R1-R9 written")
