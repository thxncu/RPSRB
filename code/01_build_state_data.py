"""01 - State-level inputs.

Builds from raw files:
  data/derived/state_panel.csv        EIA-861 historical state data (Total Electric Industry), 1990-2024
  data/derived/henry_hub_annual.csv   annual means of EIA monthly Henry Hub spot (RNGWHHD)
  data/derived/generation_shares.csv  EIA-923 based state generation shares (total electric power industry)
  data/derived/median_income.csv      Census Historical Income Table H-8 (current dollars)
"""
import re
import numpy as np
import pandas as pd

from rpsrb.config import RAW, DER

SECTORS = {"RESIDENTIAL": "residential", "COMMERCIAL": "commercial", "INDUSTRIAL": "industrial"}
VARS = ["revenue_k", "sales_mwh", "customers", "price"]


def read_hs861(path):
    raw = pd.read_excel(path, sheet_name="Total Electric Industry", header=None)
    top = raw.iloc[0].astype(str).str.strip().str.upper()
    d = raw.iloc[3:]
    out = pd.DataFrame({"year": pd.to_numeric(d[0], errors="coerce"),
                        "state": d[1].astype(str).str.strip()})
    for sec, lab in SECTORS.items():
        c0 = int(np.where(top == sec)[0][0])
        for k, v in enumerate(VARS):
            out[f"{lab}_{v}"] = pd.to_numeric(d[c0 + k], errors="coerce")
    out = out.dropna(subset=["year"])
    out["year"] = out["year"].astype(int)
    return out[(out.state.str.len() == 2) & (out.state != "US")]


panel = pd.concat([read_hs861(RAW / "eia_state" / "HS861_1990-2009.xlsx"),
                   read_hs861(RAW / "eia_state" / "HS861_2010-.xlsx")])
panel = panel.sort_values(["state", "year"]).reset_index(drop=True)
panel["residential_bill"] = panel.residential_revenue_k * 1000 / panel.residential_customers / 12
panel["residential_use_per_customer"] = panel.residential_sales_mwh / panel.residential_customers
panel.to_csv(DER / "state_panel.csv", index=False)
print(f"state_panel: {panel.state.nunique()} jurisdictions, {panel.year.min()}-{panel.year.max()}, "
      f"{len(panel)} rows")

# Henry Hub: annual mean of monthly spot prices
m = pd.read_excel(RAW / "eia_gas" / "RNGWHHDm.xls", sheet_name="Data 1", header=2)
m.columns = ["date", "hh"]
m["year"] = pd.to_datetime(m.date).dt.year
hh = m.groupby("year").hh.mean().rename("hh_usd_mmbtu").loc[1997:2024]
hh.to_frame().to_csv(DER / "henry_hub_annual.csv")
print("henry_hub_annual:", hh.loc[[2015, 2020, 2022]].round(2).to_dict())

# Generation shares
g = pd.read_excel(RAW / "eia_generation" / "annual_generation_state.xls", header=1)
g.columns = ["year", "state", "producer", "source", "gen_mwh"]
g = g[g.producer.astype(str).str.contains("Total Electric Power", na=False)]
g["state"] = g.state.astype(str).str.strip()
g = g[g.state.str.len() == 2]
piv = g.pivot_table(index=["state", "year"], columns="source", values="gen_mwh", aggfunc="sum").fillna(0)
re_cols = [c for c in piv.columns if c in ["Wind", "Solar Thermal and Photovoltaic", "Geothermal",
                                            "Wood and Wood Derived Fuels", "Other Biomass"]]
gs = pd.DataFrame({"re_share_pct": 100 * piv[re_cols].sum(axis=1) / piv["Total"],
                   "gas_share_pct": 100 * piv["Natural Gas"] / piv["Total"],
                   "coal_share_pct": 100 * piv["Coal"] / piv["Total"]}).reset_index()
gs.to_csv(DER / "generation_shares.csv", index=False)
print(f"generation_shares: {gs.state.nunique()} states, {gs.year.min()}-{gs.year.max()}")

# Census H-8 median household income, current dollars (first block of the sheet)
raw = pd.read_excel(RAW / "census" / "h08.xlsx", header=None)
ABBR = {"Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
        "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "D.C.": "DC",
        "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
        "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY",
        "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
        "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
        "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
        "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
        "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
        "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
        "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
        "Wisconsin": "WI", "Wyoming": "WY"}
years = {}
for j in range(1, raw.shape[1]):
    mt = re.match(r"^\s*(\d{4})", str(raw.iat[7, j]))
    if mt and int(mt.group(1)) not in years:      # first column for a year (2013, 2017 have two)
        years[int(mt.group(1))] = j
rows = []
for i in range(9, 61):
    st = ABBR.get(str(raw.iat[i, 0]).strip())
    if st:
        for y, j in years.items():
            rows.append({"state": st, "year": y, "median_income": pd.to_numeric(raw.iat[i, j], errors="coerce")})
inc = pd.DataFrame(rows)
inc.to_csv(DER / "median_income.csv", index=False)
print(f"median_income: {inc.state.nunique()} states, {inc.year.min()}-{inc.year.max()}")
