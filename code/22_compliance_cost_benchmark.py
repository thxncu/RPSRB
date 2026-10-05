"""22 - Accounting benchmark from LBNL compliance costs.

Tables
  C1_compliance_costs        LBNL total RPS compliance cost (% of average retail bill), Ohio and RPS donors
  C2_ohio_accounting         Ohio cost per pp of requirement x requirement cut vs original SB 221 schedule
  C4_ohio_package            other measures in the Ohio package as shares of revenue and bills (Table S12)
  C3_accounting_tests        Ohio state-level and obligated-only estimates tested against the accounting
                             benchmark; comparison with the Greenstone-Nath scaled benchmark
"""
import numpy as np
import pandas as pd
from scipy.stats import norm

from rpsrb.config import DER, DONOR_LIST, OH_ACTUAL, OH_CUT, GN_PER_PP
from rpsrb.sdid import run_case
from rpsrb.data import wide, within_panel, save

C = pd.read_csv(DER / "rps_compliance_costs.csv")
C["year"] = C.year.astype(int)
keep = ["OH", "AZ", "PA", "MO", "WI", "TX", "IA"]
save(C[C.state.isin(keep)].pivot(index="year", columns="state", values="cost_pct_bill").reset_index(),
     "C1_compliance_costs")

oh = C[C.state == "OH"].set_index("year").cost_pct_bill
rows = [{"year": y, "oh_cost_pct_bill": oh.at[y], "oh_requirement_pct": OH_ACTUAL[y],
         "cost_per_pp": oh.at[y] / OH_ACTUAL[y], "requirement_cut_pp": OH_CUT[y],
         "implied_saving_pct": oh.at[y] / OH_ACTUAL[y] * OH_CUT[y]} for y in range(2014, 2025)]
C2 = save(pd.DataFrame(rows), "C2_ohio_accounting")
acct = C2.implied_saving_pct.mean()
from rpsrb.bench import benchmarks
_b = benchmarks("OH", 2014)
gn_lo, gn_hi = -_b["gn_scaled_low"], -_b["gn_scaled_high"]
print(f"OH pre-freeze cost 2013 = {oh.at[2013]:.2f}% | accounting saving 2014-24 = {acct:.2f}% | "
      f"GN-scaled = {gn_lo:.1f}-{gn_hi:.1f}% ({gn_lo/acct:.0f}-{gn_hi/acct:.0f}x)")

lp = lambda b: np.log(1 - b / 100)
rows = []
W = within_panel()
for lab, M, dn in [("state average", wide("residential_price"), DONOR_LIST),
                   ("obligated utilities", np.log(W[W.year >= 2000].pivot(index="year", columns="state", values="p_obl")),
                    None)]:
    if dn is None:
        dn = [d for d in DONOR_LIST if d in M and M[d].notna().all()]
    r = run_case(M, "OH", 2014, dn)
    rows.append({"series": lab, "effect_pct": r["pct"], "placebo_se": r["se"],
                 "accounting_benchmark_saving_pct": acct, "p_accounting": 1 - norm.cdf((r["tau"] - lp(acct)) / r["se"]),
                 "gn_scaled_low_saving_pct": gn_lo, "gn_scaled_high_saving_pct": gn_hi,
                 "mde80_pct": 100 * (np.exp(2.8 * r["se"]) - 1),
                 "pre_freeze_cost_2013_pct": oh.at[2013]})
save(pd.DataFrame(rows), "C3_accounting_tests")

# ------------------------------------------------------------------ other measures in the Ohio package (Table S12)
# Documentary amounts (sources in config.OH_PACKAGE); shares computed from EIA state revenue and bills.
from rpsrb.config import OH_PACKAGE
from rpsrb.data import state_panel
P = state_panel().set_index(["state", "year"])
rows = []
for item in OH_PACKAGE:
    y = item["year"]
    rev = sum(P.loc[("OH", y), f"{c}_revenue_k"] for c in ["residential", "commercial", "industrial"]) * 1e3
    bill = P.loc[("OH", y), "residential_bill"]
    row = dict(item)
    if item.get("statewide_musd") is not None:
        row["share_of_retail_revenue_pct"] = 100 * item["statewide_musd"] * 1e6 / rev
    for k in ("res_low_usd_month", "res_high_usd_month"):
        if item.get(k) is not None:
            row[k.replace("usd_month", "pct_of_avg_bill")] = 100 * item[k] / bill
    row["oh_avg_residential_bill_usd"] = bill
    rows.append(row)
save(pd.DataFrame(rows), "C4_ohio_package")
