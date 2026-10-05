"""10 - Main SDID estimates and robustness battery (state level).

Tables written to output/tables:
  T2_main_estimates          price and bill effects, placebo SE/p, 95% CI, detection threshold
  T2_pooled_means            descriptive means across episodes (log-point averages)
  S2_robustness              leave-one-out, donor subgroups, in-time placebo, conformal (3 statistics),
                             anticipation, DiD, classic synthetic control, own-state adoption-period runs, commercial, industrial, use per customer,
                             Ohio pre-HB6 truncation, WV trend adjustment, detection threshold
  S3_weights_fit             top donor weights, pre-RMSPE, post/pre ratio, bill pre-RMSPE
  S5_ohio_annual_gaps        raw treated-minus-synthetic gaps (Supplementary Table S5b, raw-gap columns)
"""
import numpy as np
import pandas as pd

from rpsrb.config import TREATED, DONOR_LIST, DONORS, CAUSAL
from rpsrb.sdid import run_case, run_sc, fit, pct, conformal_p, rmspe_ratio_test
from rpsrb.data import wide, state_panel, save

P = state_panel()
LOGP, LOGB = wide("residential_price", panel=P), wide("residential_bill", panel=P)
LOGC, LOGI = wide("commercial_price", panel=P), wide("industrial_price", panel=P)
LOGU = wide("residential_use_per_customer", panel=P)

# ------------------------------------------------------------------ Table 2
rows, cases = [], {}
for lab, M in [("price", LOGP), ("bill", LOGB)]:
    for s, t in TREATED.items():
        r = run_case(M, s, t, DONOR_LIST, keep_paths=True)
        cases[(lab, s)] = r
        rows.append({"outcome": lab, "state": s, "onset": t, "pre_years": r["T0"], "post_years": r["T1"],
                     "tau_log": r["tau"], "effect_pct": r["pct"], "placebo_se": r["se"], "p_placebo": r["p"],
                     "ci95_lo_pct": r["ci_lo"], "ci95_hi_pct": r["ci_hi"],
                     "detection_threshold_2se_pct": pct(2 * r["se"]),
                     "mde80_2.8se_pct": pct(2.8 * r["se"]), "n_donors": len(r["donors"])})
T2 = save(pd.DataFrame(rows), "T2_main_estimates")
pooled = []
for lab in ["price", "bill"]:
    x = T2[T2.outcome == lab]
    pooled += [{"outcome": lab, "set": "OH, KS, MT", "mean_pct_log_avg": pct(x[x.state.isin(CAUSAL)].tau_log.mean())},
               {"outcome": lab, "set": "all four", "mean_pct_log_avg": pct(x.tau_log.mean()),
                "mean_pct_simple_avg": x.effect_pct.mean()}]
save(pd.DataFrame(pooled), "T2_pooled_means")
print(T2[["outcome", "state", "effect_pct", "p_placebo", "ci95_lo_pct", "ci95_hi_pct"]].round(2).to_string(index=False))

# ------------------------------------------------------------------ S2 robustness battery (price)
never = [d for d, v in DONORS.items() if v == "never"]
vol = [d for d, v in DONORS.items() if v == "voluntary"]
stable = [d for d, v in DONORS.items() if v == "stable"]
# Earlier-period runs at the state's own policy dates: OH SB 221 (2008), KS RES Act (2009), WV portfolio act
# (2009), MT 15% requirement step (2015). These are own-state estimates around adoption, not placebos.
INTIME = {"OH": (2008, 2013), "KS": (2009, 2014), "WV": (2009, 2014), "MT": (2015, 2020)}
# Placebo dates with no compliance obligation in any treated state (first compliance: MT 2008, OH 2009, KS 2011).
PLACEBO = (2004, 2007)
rob = []


def add(check, s, val, p=np.nan):
    rob.append({"check": check, "state": s, "value": val, "p": p})


for s, t in TREATED.items():
    base = cases[("price", s)]
    add("Baseline SDID (%)", s, base["pct"], base["p"])
    loo = [pct(fit(LOGP, s, t, [d for d in DONOR_LIST if d != x])["tau"]) for x in DONOR_LIST]
    add("Leave-one-out min (%)", s, min(loo))
    add("Leave-one-out max (%)", s, max(loo))
    for name, dl in [("Never-RPS donors only (%)", never), ("Voluntary-goal donors only (%)", vol),
                     ("Stable-mandate donors only (%)", stable),
                     ("Excluding AZ (%)", [d for d in DONOR_LIST if d != "AZ"]),
                     ("Excluding TX (%)", [d for d in DONOR_LIST if d != "TX"])]:
        add(name, s, pct(fit(LOGP, s, t, dl)["tau"]))
    ft, end = INTIME[s]
    r = run_case(LOGP, s, ft, DONOR_LIST, end=end)
    add(f"Own-state adoption period, onset {ft}, window to {end} (%)", s, r["pct"], r["p"])
    r = run_case(LOGP, s, PLACEBO[0], DONOR_LIST, end=PLACEBO[1])
    add(f"In-time placebo, onset {PLACEBO[0]}, window to {PLACEBO[1]} (%)", s, r["pct"], r["p"])
    for stat in ["abs_mean", "q1", "q2"]:
        add(f"Conformal p ({stat})", s, conformal_p(LOGP, s, t, DONOR_LIST, stat))
    add("Anticipation, onset one year earlier (%)", s, pct(fit(LOGP, s, t - 1, DONOR_LIST)["tau"]))
    f = fit(LOGP, s, t, DONOR_LIST)
    T0, yt = f["T0"], f["y_treated"]
    Yc = LOGP.loc[f["years"], f["donors"]].T.values
    dm = Yc.mean(axis=0)
    add("Difference-in-differences, donor mean (%)", s,
        pct((yt[T0:].mean() - yt[:T0].mean()) - (dm[T0:].mean() - dm[:T0].mean())))
    sc = run_sc(LOGP, s, t, DONOR_LIST)
    add("Synthetic control (classic), mean post gap (%)", s, sc["pct"], sc["p"])
    add("Synthetic control (classic), pre-RMSPE (%)", s, sc["pre_rmspe_pct"])
    g = f["gap"]
    b = np.polyfit(np.arange(T0), g[:T0], 1)
    add("Pre-trend projection adjustment (%)", s, pct((g[T0:] - np.polyval(b, np.arange(T0, len(g)))).mean()))
    for name, M in [("Commercial price (%)", LOGC), ("Industrial price, descriptive (%)", LOGI),
                    ("Residential use per customer (%)", LOGU)]:
        r = run_case(M, s, t, DONOR_LIST)
        add(name, s, r["pct"], r["p"])
    add("Detection threshold, 2 x placebo SE (%)", s, pct(2 * base["se"]))
r = run_case(LOGP, "OH", 2014, DONOR_LIST, end=2018)
add("Post-window truncated 2018, pre HB 6 (%)", "OH", r["pct"], r["p"])
S2 = save(pd.DataFrame(rob), "S2_robustness")

# ------------------------------------------------------------------ S3 weights and fit
rows = []
for s, t in TREATED.items():
    r = cases[("price", s)]
    top = r["omega"].sort_values(ascending=False).head(5)
    rt = rmspe_ratio_test(r)
    rtb = rmspe_ratio_test(cases[("bill", s)])
    rows.append({"state": s, "top5_weights": ", ".join(f"{k} {v:.2f}" for k, v in top.items()),
                 **rt, "bill_pre_rmspe_pct": rtb["pre_rmspe_pct"],
                 "bill_pre_mspe_over_median": rtb["pre_mspe_over_median"]})
save(pd.DataFrame(rows), "S3_weights_fit")

# ------------------------------------------------------------------ S5 Ohio annual raw gaps
r = cases[("price", "OH")]
yrs = r["years"]
save(pd.DataFrame({"year": yrs, "raw_gap_pct": pct(r["gap"]), "annual_effect_pct": pct(r["annual"])})
     .query("year >= 2014"), "S5_ohio_annual_gaps")
print("S2/S3/S5 written")
