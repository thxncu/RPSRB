"""Paths, sample definitions and fixed constants for the RPSRB replication package.

Every constant that encodes a research decision lives here, with its source.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
DER = ROOT / "data" / "derived"
TAB = ROOT / "output" / "tables"
FIG = ROOT / "output" / "figures"
for _p in (DER, TAB, FIG):
    _p.mkdir(parents=True, exist_ok=True)

EST_START = 2000          # first year entering SDID estimation
SEED = 20261004           # all bootstrap / random draws

# ---------------------------------------------------------------- treated episodes
# Onset = first calendar year affected by the enacted retrenchment.
TREATED = {"OH": 2014,    # SB 310 freeze (enacted June 2014); HB 6 (2019) cut terminal target
           "KS": 2015,    # SB 91 converts RES to voluntary goal (May 2015)
           "WV": 2015,    # HB 2001 repeal (Feb 2015); not an RPS state in LBNL data -> descriptive only
           "MT": 2021}    # HB 576 repeal (2021)
CAUSAL = ["OH", "KS", "MT"]

# ---------------------------------------------------------------- donor pool (24 states)
DONORS = {
    # no standard or goal before 2010 (AK adopted a non-binding goal in 2010)
    "AL": "never", "AK": "never", "AR": "never", "FL": "never", "GA": "never", "ID": "never",
    "KY": "never", "LA": "never", "MS": "never", "NE": "never", "TN": "never", "WY": "never",
    # voluntary goals only
    "IN": "voluntary", "ND": "voluntary", "SD": "voluntary", "OK": "voluntary", "UT": "voluntary",
    "SC": "voluntary",
    # mandatory standards whose requirement schedules were set before the earliest episode (2014);
    # TX repealed its standard effective Sept 2023 (HB 1500; dropped in a robustness check).
    # TX, PA, MO also appear as adoption cohorts in script 23.
    "TX": "stable", "IA": "stable", "WI": "stable", "PA": "stable", "MO": "stable", "AZ": "stable",
}
DONOR_LIST = list(DONORS)
# Donors whose targets reached a terminal year inside the window (exclusion check, Table S2)
EXPIRING = ["PA", "MO", "WI", "OK", "ND", "SD"]
EXCLUDED_FROM_POOL = {"NC": "HB 951 (2021) major strengthening", "MN": "HF 7 (2023) major strengthening"}

# ---------------------------------------------------------------- Ohio requirement schedules (% of retail sales)
# Original SB 221 (2008) renewable benchmark: 2.5% in 2014 rising 1 pp/yr to 12.5% in 2024.
OH_ORIGINAL = {y: 2.5 + (y - 2014) for y in range(2014, 2025)}
# Enacted schedule after SB 310 / HB 6, Ohio Revised Code 4928.64 (also LBNL June 2026 file).
OH_ACTUAL = {2014: 2.5, 2015: 2.5, 2016: 2.5, 2017: 3.5, 2018: 4.5, 2019: 5.5, 2020: 5.5,
             2021: 6.0, 2022: 6.5, 2023: 7.0, 2024: 7.5}
OH_CUT = {y: OH_ORIGINAL[y] - OH_ACTUAL[y] for y in OH_ORIGINAL}

# ---------------------------------------------------------------- adoption-side benchmark
# Greenstone & Nath, "Do Renewable Portfolio Standards Deliver Cost-Effective Carbon Abatement?",
# version of 12 Nov 2021: +11% at year 7 (net requirement 2.2 pp), +17% at year 12 (5.0 pp).
GN_PATH = {0: 0.0, 7: 11.0, 12: 17.0}
GN_PER_PP = (17.0 / 5.0, 11.0 / 2.2)     # 3.4 and 5.0 percent per pp of net requirement
# LBNL 2026 data update: "RPS compliance costs averaged roughly 5% of retail electricity bills across
# states ... based on the most recent year of available data (typically 2024 or 2025)".
LBNL_AVG = 5.0

# ---------------------------------------------------------------- utility-level groups
# Groups exempt from the RPS obligation in each treated / adoption state (LBNL notes; state statutes).
EXEMPT_GROUPS = {**{s: ["Coop", "Public"] for s in ["IL", "ME", "MO", "NJ", "NV", "OH", "PA", "RI",
                                                    "TX", "IA", "CT", "MA", "KS", "VA", "MT"]},
                 **{s: ["Public"] for s in ["AZ", "NM", "NH"]}}

# ---------------------------------------------------------------- adoption event study
ADOPTION_COHORTS = {"TX": 2002, "MA": 2003, "NV": 2003, "NM": 2006, "PA": 2007, "MT": 2008,
                    "IL": 2009, "OH": 2009, "KS": 2011, "MO": 2011, "VA": 2021}
ADOPTION_CENSOR = {"KS": 2015, "MT": 2021}     # drop years from repeal onward
NEVER_RPS_CONTROLS = ["AL", "AR", "FL", "GA", "ID", "KY", "LA", "MS", "WY", "IN", "ND", "SD",
                      "OK", "UT", "SC"]
RESTRUCTURED = ["TX", "MA", "PA", "IL", "OH"]

# ---------------------------------------------------------------- other measures in the Ohio package (Table S12)
# Statewide costs: PUCO Chair S. Randazzo, prepared statement on SB 346, 23 Sep 2020, Attachments C and D.
# Residential charges by utility (2019): Statehouse News Bureau, "Ohio's new energy law: what you should know",
# 26 Jul 2019. HB 6 charge caps: R.C. 3706.46 and 4928.148 as enacted by HB 6 (2019). OVEC 2024 range: Ohio
# Capital Journal, 23 Aug 2024, citing PUCO data. Nuclear charge enjoined 21 Dec 2020 (Franklin County Court of
# Common Pleas) and repealed by HB 128 (2021); OVEC rider ended 14 Aug 2025 under HB 15 (2025).
OH_PACKAGE = [
    {"component": "RPS (alternative energy) riders", "year": 2019, "statewide_musd": 65.5,
     "res_low_usd_month": 0.10, "res_high_usd_month": 1.17},
    {"component": "Energy-efficiency and peak-demand riders", "year": 2019, "statewide_musd": 301.5,
     "res_low_usd_month": 1.79, "res_high_usd_month": 6.67},
    {"component": "Nuclear generation charge (scheduled)", "year": 2020, "statewide_musd": None,
     "res_low_usd_month": 0.85, "res_high_usd_month": 0.85},
    {"component": "Solar generation charge (cap)", "year": 2021, "statewide_musd": None,
     "res_low_usd_month": None, "res_high_usd_month": 0.10},
    {"component": "Legacy generation (OVEC coal) rider", "year": 2024, "statewide_musd": None,
     "res_low_usd_month": 1.30, "res_high_usd_month": 1.50},
]
