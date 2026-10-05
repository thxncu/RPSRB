"""11 - Timing, generation composition, fuel-cost pass-through, and income-relative burden.

Tables
  T3_timing_composition   Panel A: price effect with post window truncated in 2020; mean raw gap 2021-24.
                          Panel B: SDID first stage on non-hydro renewable and gas generation shares (pp).
  S6_passthrough          gas-share x Henry Hub pass-through (state & year FE, clustered SE),
                          coal-heavy exclusion, Ohio fuel-channel decomposition.
  S4_burden               SDID on log(annual bill / state median income), baseline and 3-yr MA income.
"""
import numpy as np
import pandas as pd

from rpsrb.config import TREATED, DONOR_LIST
from rpsrb.sdid import run_case, fit, pct
from rpsrb.data import wide, henry_hub, generation_shares, income, save

LOGP = wide("residential_price")
G = generation_shares()
RE, GAS, COAL = G["re_share_pct"], G["gas_share_pct"], G["coal_share_pct"]
dn_gen = [d for d in DONOR_LIST if d in RE.columns]

# ------------------------------------------------------------------ Table 3
rows = []
for s, t in TREATED.items():
    row = {"state": s}
    if t <= 2018:
        r = run_case(LOGP, s, t, DONOR_LIST, end=2020)
        row.update(price_to2020_pct=r["pct"], price_to2020_p=r["p"])
    f = fit(LOGP, s, t, DONOR_LIST)
    sel = (f["years"] >= 2021) & (f["years"] <= 2024)
    row["mean_raw_gap_2021_24_pct"] = pct(f["gap"][sel]).mean()
    for lab, M in [("re_share", RE), ("gas_share", GAS)]:
        r = run_case(M, s, t, dn_gen)
        row[f"{lab}_pp"], row[f"{lab}_p"] = r["tau"], r["p"]
    rows.append(row)
T3 = save(pd.DataFrame(rows), "T3_timing_composition")
print(T3.round(2).to_string(index=False))

# ------------------------------------------------------------------ pass-through
hh = henry_hub()
gs, cs = GAS / 100, COAL / 100
dlp, dlh = LOGP.diff(), np.log(hh).diff()


def passthrough(states):
    rows = []
    for s in states:
        for t in range(2003, 2025):
            if np.isnan(dlp.at[t, s]) or np.isnan(gs.at[t - 1, s]):
                continue
            rows.append({"s": s, "t": t, "y": dlp.at[t, s], "x0": gs.at[t - 1, s] * dlh.at[t],
                         "x1": gs.at[t - 1, s] * dlh.at[t - 1], "x2": gs.at[t - 1, s] * dlh.at[t - 2]})
    d = pd.DataFrame(rows)
    for c in ["y", "x0", "x1", "x2"]:            # two-way within transformation (balanced panel)
        d[c] = d[c] - d.groupby("s")[c].transform("mean")
        d[c] = d[c] - d.groupby("t")[c].transform("mean")
    X = np.column_stack([np.ones(len(d)), d[["x0", "x1", "x2"]].values])
    b, *_ = np.linalg.lstsq(X, d.y.values, rcond=None)
    e = d.y.values - X @ b
    XX = np.linalg.inv(X.T @ X)
    meat = sum(np.outer(v, v) for v in
               (X[(d.s == s).values].T @ e[(d.s == s).values] for s in d.s.unique()))
    Gc = d.s.nunique()
    V = XX @ meat @ XX * Gc / (Gc - 1)
    se = np.sqrt(np.diag(V))
    w = np.array([0, 1, 1, 1.0])
    return b, se, b @ w, np.sqrt(w @ V @ w), len(d)


states = [c for c in LOGP.columns if c in gs.columns]
b, se, cum, cse, n = passthrough(states)
rows = [{"quantity": f"lag {k}", "estimate": b[k + 1], "se_cluster": se[k + 1], "t": b[k + 1] / se[k + 1]}
        for k in range(3)]
rows.append({"quantity": "cumulative", "estimate": cum, "se_cluster": cse,
             "ci95_lo": cum - 1.96 * cse, "ci95_hi": cum + 1.96 * cse, "n": n})
heavy = [s for s in states if cs.loc[2003:2024, s].mean() >= 0.40]
_, _, cum2, cse2, n2 = passthrough([s for s in states if s not in heavy])
rows.append({"quantity": f"cumulative, excl. {len(heavy)} coal-heavy states", "estimate": cum2,
             "se_cluster": cse2, "n": n2})
f = fit(LOGP, "OH", 2014, DONOR_LIST)
dexp = gs["OH"] - (gs[f["omega"].index] * f["omega"].values).sum(axis=1)
obs = pd.Series(pct(f["gap"]), index=f["years"])
for t in [2022, 2023, 2024]:
    fuel = 100 * (b[1] * dexp.at[t - 1] * dlh.at[t] + b[2] * dexp.at[t - 1] * dlh.at[t - 1]
                  + b[3] * dexp.at[t - 1] * dlh.at[t - 2])
    rows.append({"quantity": f"Ohio gap change {t}: observed", "estimate": obs.diff().at[t]})
    rows.append({"quantity": f"Ohio gap change {t}: fuel-predicted", "estimate": fuel})
save(pd.DataFrame(rows), "S6_passthrough")
print(pd.DataFrame(rows)[["quantity", "estimate", "se_cluster"]].round(3).to_string(index=False))

# ------------------------------------------------------------------ burden
INC = income()
bill = wide("residential_bill", log=False) * 12
common = [s for s in bill.columns if s in INC.columns]
dn = [d for d in DONOR_LIST if d in common]
rows = []
for lab, inc in [("baseline", INC), ("income 3-yr centred MA", INC.rolling(3, center=True, min_periods=2).mean())]:
    burden = (np.log(bill[common]) - np.log(inc[common])).dropna()
    for s, t in TREATED.items():
        r = run_case(burden, s, t, dn)
        rows.append({"income": lab, "state": s, "effect_pct": r["pct"], "p": r["p"]})
save(pd.DataFrame(rows), "S4_burden")
print(pd.DataFrame(rows).round(2).to_string(index=False))
