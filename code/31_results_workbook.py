"""31 - Collect every CSV in output/tables into one Excel workbook with a notes sheet."""
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

from rpsrb.config import TAB, ROOT

NOTES = {
    "T2_main_estimates": "Main SDID estimates, 24 donors, placebo inference (Table 2).",
    "T2_pooled_means": "Descriptive means of episode estimates, averaged in log points.",
    "S2_robustness": "Robustness battery (Table S2): donor subsets, in-time placebo (2004), own-state adoption-period runs, classic synthetic control, conformal p for three test statistics.",
    "S3_weights_fit": "Donor weights, pre-RMSPE, Abadie post/pre RMSPE ratio test (Table S3).",
    "S5_ohio_annual_gaps": "Ohio raw gaps and lambda-adjusted annual effects (Supplementary Table S5b).",
    "T3_timing_composition": "Table 3: truncated windows, 2021-24 gaps, generation-composition first stage.",
    "S6_passthrough": "Fuel-cost pass-through (clustered SE) and Ohio decomposition (Table S6).",
    "S4_burden": "Income-relative burden proxy (Table S4).",
    "R1_annual_effects": "Annual effects with year-specific donor placebo bands and benchmark paths.",
    "R2_benchmarks": "Symmetric-reversal benchmarks (% price change): Barbose, G&N horizon-matched, G&N scaled (OH).",
    "R3_benchmark_tests": "One-sided p for H0: savings >= benchmark (p_: normal approx.; prank_: placebo rank); 90% CI; TOST margin (%).",
    "R4_ohio_windows": "Ohio tests and bounds with post windows ending 2018 and 2020-2024 (Table S7a).",
    "R5_pooled": "Pooled OH/KS/MT with joint donor placebo distribution.",
    "R6_donor_exclusions": "Dropping donors with terminal-year targets.",
    "R7_ohio_breakdown": "Coverage x elasticity; HB 6 rider offset the Ohio rejection can absorb.",
    "R9_ohio_rank_loo": "Ohio benchmark tests with each donor dropped in turn (Table S7c).",
    "R8_kansas_onset": "Kansas with onset 2015 (LBNL: no obligations from 2015) and 2016 (SB 91 effective 1 Jan 2016).",
    "U1_coverage": "Share of residential MWh: obligated (IOU + suppliers), co-ops, public, short-form adj.",
    "U2_coverage_adjusted": "Benchmarks multiplied by obligated share.",
    "U3_obligated_only": "SDID on obligated-utility price.",
    "U4_within_state": "Within-state obligated-minus-exempt SDID; exempt definitions and donor sets.",
    "U5_ohio_decomposition": "Ohio annual effects: state, obligated, exempt, within difference (20 donors).",
    "C1_compliance_costs": "LBNL compliance cost, % of average retail bill.",
    "C2_ohio_accounting": "Ohio accounting saving = cost per pp x requirement cut.",
    "C4_ohio_package": "Other measures in the Ohio package: documentary amounts (sources in config.OH_PACKAGE) as shares of EIA revenue and bills (Table S12).",
    "C3_accounting_tests": "Ohio estimates vs accounting and G&N-scaled benchmarks; MDE at 80% power.",
    "A1_adoption_event_study": "Adoption event study (feasibility check; pre-trends present).",
    "A2_adoption_split": "Adoption event study by restructuring status.",
    "Z_manuscript_check": "Reproduced values vs numbers printed in the manuscript and supplementary material.",
}
out = ROOT / "output" / "RPSRB_results.xlsx"
with pd.ExcelWriter(out) as w:
    pd.DataFrame([{"sheet": k, "contents": v} for k, v in NOTES.items()]).to_excel(w, sheet_name="Notes", index=False)
    for k in NOTES:
        if not (TAB / f"{k}.csv").exists():
            continue
        pd.read_csv(TAB / f"{k}.csv").round(4).to_excel(w, sheet_name=k[:31], index=False)
wb = load_workbook(out)
for ws in wb:
    for row in ws.iter_rows():
        for c in row:
            c.font = Font(name="Arial", size=10, bold=(c.row == 1))
    for c in ws[1]:
        c.fill = PatternFill("solid", fgColor="E8E8E8")
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(max(10, max(len(str(c.value or "")) for c in col) + 2), 60)
    ws.freeze_panes = "A2"
ws = wb["Notes"]
ws.column_dimensions["B"].width = 100
for c in ws["B"]:
    c.alignment = Alignment(wrap_text=True, vertical="top")
wb.save(out)
print("workbook:", out)
