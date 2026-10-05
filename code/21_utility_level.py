"""21 - Utility-level analyses: obligated coverage, obligated-only estimates, within-state design.

Tables
  U1_coverage               share of state residential MWh by group (obligated IOU+suppliers, co-ops,
                            public, short-form adjustment) for the four treated states
  U2_coverage_adjusted      state-level estimate tested against benchmarks scaled by obligated share
  U3_obligated_only         SDID on the obligated-utility price (22 donors with an obligated series),
                            with benchmark tests; Ohio windows
  U4_within_state           SDID on log(obligated price) - log(exempt price), three exempt definitions,
                            two donor sets
  U5_ohio_decomposition     Ohio annual effects for state average, obligated, exempt and within-state
                            difference on a common donor set (20 states)
"""
import numpy as np
import pandas as pd
from scipy.stats import norm

from rpsrb.config import TREATED, DONOR_LIST, OH_CUT, GN_PATH, GN_PER_PP, LBNL_AVG
from rpsrb.sdid import run_case, fit, pct
from rpsrb.data import wide, within_panel, utility_panel, state_panel, save

W = within_panel()
W = W[W.year >= 2000]
U = utility_panel()
S = state_panel()
from rpsrb.bench import benchmarks, one_sided_p as osp, rank_p as rkp, scale_pct

# ------------------------------------------------------------------ coverage
E = (U[U.part.isin(["A", "B", "D"])].groupby(["state", "year", "group"]).mwh.sum()
     .unstack(fill_value=0).reset_index().merge(S[["state", "year", "residential_sales_mwh"]], on=["state", "year"]))
for c in ["IOU", "Supplier", "AdjBCD_supplier", "Coop", "Public", "AdjA_shortform", "Other"]:
    E[c + "_share"] = E.get(c, 0) / E.residential_sales_mwh
E["obligated_share"] = E.IOU_share + E.Supplier_share + E.AdjBCD_supplier_share
cov = E[E.state.isin(TREATED)][["state", "year", "obligated_share", "Coop_share", "Public_share",
                                "AdjA_shortform_share", "Other_share"]]
save(cov, "U1_coverage")
post_cov = {s: cov[(cov.state == s) & (cov.year >= t)].obligated_share.mean() for s, t in TREATED.items()}
print("post-period obligated share:", {k: round(v, 3) for k, v in post_cov.items()})

# ------------------------------------------------------------------ coverage-adjusted tests
LOGP = wide("residential_price")
rows = []
for s, t in TREATED.items():
    r = run_case(LOGP, s, t, DONOR_LIST)
    c = post_cov[s]
    B = benchmarks(s, t)
    row = {"state": s, "obligated_share_post": c, "effect_pct": r["pct"]}
    for k, v in B.items():
        row[f"bench_{k}_x_share"] = scale_pct(v, c)
        row[f"p_{k}"] = osp(r["tau"], r["se"], scale_pct(v, c))
        row[f"prank_{k}"] = rkp(r["tau"], r["placebos"], scale_pct(v, c))
    rows.append(row)
save(pd.DataFrame(rows), "U2_coverage_adjusted")

# ------------------------------------------------------------------ obligated-only
OBLP = np.log(W.pivot(index="year", columns="state", values="p_obl"))
dn_obl = [d for d in DONOR_LIST if d in OBLP and OBLP[d].notna().all()]
rows = []
for s, t in TREATED.items():
    for end in ([2018, 2020, 2021, 2024] if s == "OH" else [2024]):
        r = run_case(OBLP, s, t, dn_obl, end=end)
        yrs = range(t, end + 1)
        B = benchmarks(s, t, end)
        rows.append({"state": s, "window": f"{t}-{end}", "n_donors": len(dn_obl), "effect_pct": r["pct"],
                     "placebo_se": r["se"], "p_placebo": r["p"], "ci95_lo_pct": r["ci_lo"], "ci95_hi_pct": r["ci_hi"],
                     **{f"p_{k}": osp(r["tau"], r["se"], v) for k, v in B.items()},
                     **{f"prank_{k}": rkp(r["tau"], r["placebos"], v) for k, v in B.items()}})
U3 = save(pd.DataFrame(rows), "U3_obligated_only")
print(U3[["state", "window", "effect_pct", "ci95_lo_pct", "ci95_hi_pct"]].round(2).to_string(index=False))

# ------------------------------------------------------------------ within-state difference
obl_share = W.groupby("state").obligated_share.mean()
rows = []
for exm in ["p_exm", "p_exm_all", "p_public"]:
    D = (np.log(W.pivot(index="year", columns="state", values="p_obl"))
         - np.log(W.pivot(index="year", columns="state", values=exm)))
    full = [d for d in DONOR_LIST if d in D and D[d].notna().all()]
    restricted = [d for d in full if 0.10 <= obl_share.get(d, 0) <= 0.90]
    for dlab, dn in [("all available", full), ("obligated share 10-90%", restricted)]:
        for s, t in [("OH", 2014), ("KS", 2015), ("MT", 2021)]:
            if s not in D or D[s].isna().any():
                continue
            r = run_case(D, s, t, dn)
            rows.append({"exempt_definition": exm, "donors": dlab, "n_donors": len(dn), "state": s,
                         "effect_pct": r["pct"], "placebo_se": r["se"], "p_placebo": r["p"],
                         "ci95_lo_pct": r["ci_lo"], "ci95_hi_pct": r["ci_hi"],
                         "pre_rmspe_pct": 100 * np.sqrt(np.mean(r["gap"][:r["T0"]] ** 2))})
U4 = save(pd.DataFrame(rows), "U4_within_state")
print(U4.query("exempt_definition=='p_exm'")[["donors", "state", "effect_pct", "placebo_se", "p_placebo"]]
      .round(3).to_string(index=False))

# ------------------------------------------------------------------ Ohio decomposition, common donors
D_obl = np.log(W.pivot(index="year", columns="state", values="p_obl"))
D_exm = np.log(W.pivot(index="year", columns="state", values="p_exm"))
series = {"state_average": LOGP.loc[2000:], "obligated": D_obl, "exempt": D_exm, "within_difference": D_obl - D_exm}
common = [d for d in DONOR_LIST if all(d in M and M[d].notna().all() for M in series.values())
          and 0.10 <= obl_share.get(d, 0) <= 0.90]
rows = []
for lab, M in series.items():
    r = run_case(M, "OH", 2014, common, keep_paths=True)
    P = np.array([pf["annual"] for pf in r["placebo_fits"].values()])
    for k, y in enumerate(r["years"]):
        rows.append({"series": lab, "year": y, "effect_pct": pct(r["annual"][k]),
                     "band95_pct": pct(1.96 * P[:, k].std(ddof=1)), "avg_2014_24_pct": r["pct"], "p_avg": r["p"]})
save(pd.DataFrame(rows), "U5_ohio_decomposition")
print("common donors:", len(common), common)
