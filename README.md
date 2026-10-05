# Replication package

**Bounding the electricity price effects of rolling back renewable portfolio standards: evidence from U.S. states**

This package reproduces every table, figure and number in the manuscript and its supplementary material. One command rebuilds everything from the raw public files:

```
pip install -r requirements.txt
python code/run_all.py                 # ~7 minutes, of which ~6 are the adoption-check bootstrap
python code/run_all.py --skip-adoption # ~1 minute
```

Outputs:
- `output/tables/*.csv`: one file per table.
- `output/RPSRB_results.xlsx`: all tables, with a Notes sheet.
- `output/figures/*.png|pdf`: all figures; `Fig1-3*.tif`: 600-dpi files for journal upload.
- `output/logs/`: one log per step.

`output/tables/Z_manuscript_check.csv` compares the numbers printed in the manuscript and supplement with the reproduced values.

## Directory layout

```
code/
  rpsrb/config.py      sample definitions, schedules, benchmarks (every research decision is set here)
  rpsrb/sdid.py        SDID estimator, placebo inference, annual effects, RMSPE-ratio and conformal tests, classic SC
  rpsrb/bench.py       full-reversal benchmarks and one-sided tests
  rpsrb/data.py        loaders for derived data
  01_build_state_data.py          EIA-861 state panel, Henry Hub, generation shares, Census income
  02_build_utility_data.py        EIA-861 utility-level residential sales, ownership groups, within-state prices
  03_build_lbnl_data.py           LBNL requirements, applicability notes, compliance costs
  10_main_sdid.py                 Table 3; Supplementary Tables S2, S3, S5b (raw gaps); Fig. 1 inputs
  11_mechanisms_burden.py         Supplementary Tables S4, S5a, S6
  20_benchmarks_and_bounds.py     Tables 2 and 4; annual effects (Fig. 2, S5b); Tables S7a, S7b, S7c, S11;
                                  pooled estimate; donor exclusions (S2)
  21_utility_level.py             Table 1 coverage; Table 4 obligated rows; Tables S8a-c; Fig. 3
  22_compliance_cost_benchmark.py Tables S9a, S9b, S12; Ohio accounting benchmark
  23_adoption_event_study.py      same-sample adoption check (Table S10, Fig. S3)
  30_figures.py                   all figures
  40_check_against_manuscript.py  reproduced vs printed values
  31_results_workbook.py          Excel workbook of all tables
  run_all.py
data/raw/        public source files (see below), unmodified
data/derived/    built by scripts 01-03
docs/RESULTS_MAP.md   claims in the paper -> numbers -> output files
```

## Data sources (all public; files in `data/raw` are unmodified downloads)

| Folder | File(s) | Source |
|---|---|---|
| `eia_state` | HS861_1990-2009.xlsx, HS861_2010-.xlsx | EIA, historical state data (Form EIA-861), sheet "Total Electric Industry". https://www.eia.gov/electricity/data/state/ |
| `eia861_utility/YYYY` | Sales_Ult_Cust_YYYY (2000-2024); Utility_Data_YYYY (2000-2004, ownership only) | EIA-861 annual files ("Reformatted" zips for 2000-2011, "Original" for 2012-2024). https://www.eia.gov/electricity/data/eia861/ |
| `eia_gas` | RNGWHHDm.xls | EIA Henry Hub natural gas spot price, monthly (RNGWHHD) |
| `eia_generation` | annual_generation_state.xls | EIA net generation by state, type of producer and energy source |
| `census` | h08.xlsx | Census Historical Income Table H-8, median household income by state |
| `lbnl` | RPS_CES_Targets_and_Demand_June_2026.xlsx; Historical_RPS_CES_Target_Achievement_and_Compliance_Costs_June_2026.xlsx | LBNL, U.S. State Electricity Resource Standards: 2026 Data Update (June 2026). https://emp.lbl.gov/projects/renewables-portfolio |

## Key definitions

- **Episodes:** Ohio (start 2014; SB 310 freeze, HB 6 in 2019), Kansas (2015; conversion to a voluntary goal; 2016 in `R8_kansas_onset`), Montana (2021; repeal), West Virginia (2015; repeal; descriptive only, because LBNL does not list it as an RPS state and its pre-treatment fit fails the uniform criterion).
- **Donor pool (24 states):** 12 states with no statutory standard or goal before 2010 (Alaska adopted a non-binding goal in 2010; LBNL lists Nebraska utility-board goals starting after 2040), 6 with voluntary goals, and 6 with mandatory standards. Five mandatory donors set their requirement schedules before 2014 and did not change them through 2024; Texas repealed its standard effective September 2023 (HB 1500) and is dropped in a robustness check. Texas, Pennsylvania and Missouri began compliance in the pre-treatment period (2002, 2007, 2011) and also appear as adoption cohorts in script 23. North Carolina and Minnesota are excluded (major strengthening in 2021 and 2023), as are 21 jurisdictions that enacted or amended mandatory standards after 2010 (Supplementary Table S1).
- **Robustness:** in-time placebos at 2004 (window 2000–2007); own-state adoption-period runs at each state's earlier policy date; classic synthetic control; leave-one-donor-out permutation tests for Ohio (R9).
- **Estimation:** SDID (Arkhangelsky et al., 2021) from 2000. Inference by in-place placebos (24 donors): SE = SD of placebo estimates; 95% CI = tau ± 1.96 SE; exact-style p minimum 0.04. Annual effects are gaps minus the lambda-weighted pre-period gap, so their post-period mean equals tau.
- **Benchmark tests:** one-sided tests of H0: savings ≥ benchmark, by normal approximation with the placebo SE (`p_*`) and by placebo rank (`prank_*`, minimum 0.04). `normal_lower_bound95_pct` and `rank_lower_bound_pct` are the corresponding one-sided bounds. Equivalence margins (TOST, 90% CI) are in percent.
- **Benchmarks:** LBNL 2026 national average compliance cost (~5% of bills); Ohio accounting saving (LBNL cost per point of requirement × requirement cut relative to the original SB 221 schedule); Greenstone–Nath adoption path (11% at year 7, 17% at year 12, linear in log points), horizon-matched and, for Ohio, scaled by the requirement cut at 3.4–5.0% per point. A price increase of X% is reversed as a fall of X/(1+X), and averages over years are taken in log points (`rpsrb/bench.py`).
- **Obligated vs exempt utilities:** obligated = investor-owned utilities and retail suppliers; exempt = municipal and cooperative utilities (municipals only in AZ, NM, NH), balanced panel of utilities reporting long-form residential data in all 25 years. Ownership for 2000-2004 is merged from Utility_Data by utility number.

## Software

Tested with Python 3.13.16, numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, matplotlib 3.11.2, openpyxl 3.1.5 and xlrd 2.0.2. Results are deterministic; bootstrap draws use the fixed seed in `config.SEED`. EIA-861 utility revenue and MWh reconcile with state totals within 0.2% in every state-year.
