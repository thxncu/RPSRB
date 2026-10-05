"""02 - Utility-level residential data from EIA-861 'Sales to Ultimate Customers' files, 2000-2024.

Outputs
  data/derived/utility_residential.csv   one row per utility x state x part x year, with ownership group
  data/derived/within_state_prices.csv   state-year prices for RPS-obligated vs exempt utilities

Conventions
  * Parts: A = bundled, B = energy-only (retail suppliers), C = delivery-only, D = bundled by retail suppliers.
    MWh are taken from parts A, B, D (part C repeats part B volumes); revenue from all parts.
  * 2000-2004 sales files carry no ownership field; it is merged from Utility_Data_YYYY.
  * Utility number 99999 rows are EIA state adjustments: part A rows stand in for short-form
    (EIA-861S) utilities -- small municipals and co-ops -- and parts B-D for retail-supplier volumes.
  * Exempt group price uses a balanced panel of municipal/co-op utilities that file long-form
    residential data in all 25 years, so composition does not change when EIA moved small
    utilities to the short form (2012-2018, 2020-2024).
"""
import numpy as np
import pandas as pd

from rpsrb.config import RAW, DER, EXEMPT_GROUPS

YEARS = range(2000, 2025)


def _col(hdr, name):
    m = [i for i, h in enumerate(hdr) if h.lower().startswith(name.lower())]
    return m[0] if m else None


rows = []
for y in YEARS:
    f = next((RAW / "eia861_utility" / str(y)).glob(f"Sales_Ult_Cust_{y}.xls*"))
    raw = pd.read_excel(f, sheet_name="States", header=None)
    top = raw.iloc[0].astype(str).str.upper().str.strip()
    hdr = raw.iloc[2].astype(str).str.strip().tolist()
    r0 = int(np.where(top == "RESIDENTIAL")[0][0])
    d = raw.iloc[3:]
    out = pd.DataFrame({"year": y,
                        "uid": pd.to_numeric(d[_col(hdr, "Utility Number")], errors="coerce"),
                        "name": d[_col(hdr, "Utility Name")].astype(str).str.strip(),
                        "state": d[_col(hdr, "State")].astype(str).str.strip(),
                        "part": d[_col(hdr, "Part")].astype(str).str.strip(),
                        "rev_k": pd.to_numeric(d[r0], errors="coerce"),
                        "mwh": pd.to_numeric(d[r0 + 1], errors="coerce"),
                        "customers": pd.to_numeric(d[r0 + 2], errors="coerce")})
    oc = _col(hdr, "Ownership")
    if oc is not None:
        out["ownership"] = d[oc].astype(str).str.strip().values
    else:
        u = pd.read_excel(next((RAW / "eia861_utility" / str(y)).glob(f"Utility_Data_{y}.xls*")),
                          sheet_name="States", header=1)
        u = u.rename(columns=lambda c: str(c).strip())[["Utility Number", "State", "Ownership Type"]]
        u.columns = ["uid", "state", "ownership"]
        u["uid"] = pd.to_numeric(u.uid, errors="coerce")
        u["state"] = u.state.astype(str).str.strip()
        u["ownership"] = u.ownership.astype(str).str.strip()
        # Ownership is a utility attribute; Utility_Data lists multistate utilities once (home state),
        # so merge on utility number, preferring the same-state record when one exists.
        by_state = u.drop_duplicates(["uid", "state"]).rename(columns={"ownership": "own_s"})
        by_uid = u.drop_duplicates("uid")[["uid", "ownership"]].rename(columns={"ownership": "own_u"})
        out = out.merge(by_state, on=["uid", "state"], how="left").merge(by_uid, on="uid", how="left")
        out["ownership"] = out.own_s.fillna(out.own_u)
        out = out.drop(columns=["own_s", "own_u"])
    rows.append(out[(out.state.str.len() == 2) & out.uid.notna()])
U = pd.concat(rows, ignore_index=True)


def group(r):
    o = str(r.ownership)
    if r.uid == 99999:
        return "AdjA_shortform" if r.part == "A" else "AdjBCD_supplier"
    if o in ("Investor Owned", "Private"):
        return "IOU"
    if "Marketer" in o or o == "Community Choice Aggregator":
        return "Supplier"
    if o == "Cooperative":
        return "Coop"
    if o in ("Municipal", "Political Subdivision", "Political Sub-Division", "State", "Federal"):
        return "Public"
    return "Other"


U["group"] = U.apply(group, axis=1)
U.to_csv(DER / "utility_residential.csv", index=False)

# reconciliation with state totals
S = pd.read_csv(DER / "state_panel.csv")[["state", "year", "residential_revenue_k", "residential_sales_mwh"]]
agg = (U.groupby(["state", "year"])
       .apply(lambda x: pd.Series({"rev": x.rev_k.sum(), "mwh": x[x.part.isin(["A", "B", "D"])].mwh.sum()}))
       .reset_index().merge(S, on=["state", "year"]))
print("utility rows:", len(U), "| reconciliation revenue max |rel diff| =",
      f"{(agg.rev / agg.residential_revenue_k - 1).abs().max():.2e}",
      "| MWh =", f"{(agg.mwh / agg.residential_sales_mwh - 1).abs().max():.2e}")

# obligated (IOU + retail suppliers) price by state-year
OBL = ["IOU", "Supplier", "AdjBCD_supplier"]
ob = (U[U.group.isin(OBL)].groupby(["state", "year"])
      .apply(lambda x: pd.Series({"rev_obl": x.rev_k.sum(),
                                  "mwh_obl": x[x.part.isin(["A", "B", "D"])].mwh.sum()}))
      .reset_index())
ob["p_obl"] = ob.rev_obl / ob.mwh_obl * 100

# exempt balanced panel (part A, positive sales and revenue every year)
e = U[(U.part == "A") & (U.mwh > 0) & (U.rev_k > 0) & U.group.isin(["Coop", "Public"])]
n_years = e.groupby(["state", "uid", "group"]).year.nunique()
bal = n_years[n_years == len(YEARS)].reset_index()[["state", "uid", "group"]]
eb = e.merge(bal, on=["state", "uid", "group"])


def exempt_price(df, label):
    g = df.groupby(["state", "year"]).agg(rev=("rev_k", "sum"), mwh=("mwh", "sum"), n=("uid", "nunique"))
    g[label] = g.rev / g.mwh * 100
    return g


rows = []
for s in sorted(U.state.unique()):
    groups = EXEMPT_GROUPS.get(s, ["Coop", "Public"])
    x = eb[(eb.state == s) & eb.group.isin(groups)]
    if len(x):
        g = exempt_price(x, "p_exm").reset_index()
        g["n_exm"] = g.n
        g["mwh_exm"] = g.mwh
        rows.append(g[["state", "year", "p_exm", "n_exm", "mwh_exm"]])
EX = pd.concat(rows)
pub = exempt_price(eb[eb.group == "Public"], "p_public").reset_index()[["state", "year", "p_public"]]
allx = exempt_price(e, "p_exm_all").reset_index()[["state", "year", "p_exm_all"]]

W = (ob.merge(EX, on=["state", "year"], how="outer").merge(pub, on=["state", "year"], how="left")
     .merge(allx, on=["state", "year"], how="left").merge(S, on=["state", "year"], how="left"))
W["obligated_share"] = W.mwh_obl / W.residential_sales_mwh
W["exempt_bal_share"] = W.mwh_exm / W.residential_sales_mwh
W.to_csv(DER / "within_state_prices.csv", index=False)
print("within_state_prices:", W.state.nunique(), "states;",
      "OH obligated share 2014 =", round(W.query("state=='OH' and year==2014").obligated_share.iloc[0], 3))
