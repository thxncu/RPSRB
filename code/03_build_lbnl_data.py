"""03 - LBNL state electricity resource standards data (June 2026 update).

Outputs
  data/derived/rps_requirements_pct.csv   Total RPS (or CES) % of retail sales, state x year (wide)
  data/derived/rps_notes.csv              LBNL applicability notes by state
  data/derived/rps_compliance_costs.csv   Total RPS compliance cost, % of average retail bill (long)
"""
import numpy as np
import pandas as pd

from rpsrb.config import RAW, DER

T = pd.read_excel(RAW / "lbnl" / "RPS_CES_Targets_and_Demand_June_2026.xlsx",
                  sheet_name="RPS & CES Targets (%)", header=24)
T["State"] = T["State"].ffill()
ycols = [c for c in T.columns if str(c).replace(".0", "").isdigit()]
req, notes = {}, []
for s, g in T.groupby("State", sort=False):
    row = g[g["RPS Tier or Carve Out"].astype(str).str.strip().str.startswith("Total")].iloc[0]
    req[s] = pd.to_numeric(row[ycols], errors="coerce").values * 100
    notes.append({"state": s, "series": str(row["RPS Tier or Carve Out"]).strip(),
                  "note": " ".join(map(str, g["Special Notes"].dropna().tolist()))})
R = pd.DataFrame(req, index=[int(float(y)) for y in ycols])
R.index.name = "year"
# Pennsylvania: AEPS first compliance year is 2007; the 2002 entry reflects a pre-AEPS settlement.
R.loc[R.index < 2007, "PA"] = 0.0
R.to_csv(DER / "rps_requirements_pct.csv")
pd.DataFrame(notes).to_csv(DER / "rps_notes.csv", index=False)
print("requirements:", R.shape[1], "jurisdictions; WV listed:", "WV" in R.columns)

C = pd.read_excel(RAW / "lbnl" / "Historical_RPS_CES_Target_Achievement_and_Compliance_Costs_June_2026.xlsx",
                  sheet_name="Compliance Costs", header=23)
C["States"] = C["States"].ffill()
C = C[C["Total RPS or Tier"].astype(str).str.strip().str.startswith("Total")]
long = C.melt(id_vars=["States", "Total RPS or Tier"], var_name="year", value_name="cost")
long["cost_pct_bill"] = pd.to_numeric(long.cost, errors="coerce") * 100
long = long.rename(columns={"States": "state", "Total RPS or Tier": "series"}).drop(columns="cost")
long.to_csv(DER / "rps_compliance_costs.csv", index=False)
oh = long[long.state == "OH"].set_index("year").cost_pct_bill
print("OH compliance cost 2013:", round(oh.loc[2013], 2), "% of bill")
