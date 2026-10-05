"""30 - Figures (PNG 300 dpi and vector PDF) from the tables written by scripts 10-23."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

from rpsrb.config import TREATED, DONOR_LIST, FIG, TAB
from rpsrb.sdid import run_case, pct
from rpsrb.data import wide

BLUE, ORANGE, GREY, MUTED, INK, GRID = "#2a78d6", "#eb6834", "#c9c8c2", "#52514e", "#0b0b0b", "#e6e5e0"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})
NAMES = {"OH": "Ohio (freeze 2014)", "KS": "Kansas (voluntary goal 2015)",
         "WV": "West Virginia (repeal 2015, descriptive)", "MT": "Montana (repeal 2021)"}


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    if name.startswith("Fig") and not name.startswith("FigS"):     # journal upload files
        fig.savefig(FIG / f"{name}.tif", dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


def style(ax):
    ax.grid(axis="y", color=GRID, lw=.6)


# Fig 1 / S1 trajectories and S2 placebo histograms
for M, name, ylab in [(wide("residential_price"), "Fig1_sdid_price", "log residential price (log ¢/kWh)"),
                      (wide("residential_bill"), "FigS1_sdid_bill", "log average monthly bill (log $)")]:
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4), sharex=True)
    cases = {}
    for ax, (s, t) in zip(axes.flat, TREATED.items()):
        r = run_case(M, s, t, DONOR_LIST)
        cases[s] = r
        ax.plot(r["years"], r["y_treated"], color=INK, lw=1.6, label="Treated state")
        ax.plot(r["years"], r["synth"], color=MUTED, lw=1.4, ls="--", label="SDID synthetic")
        ax.axvline(t - .5, color=MUTED, lw=.8, ls=":")
        ax.set_title(NAMES[s], fontsize=9, loc="left")
        style(ax)
    axes[0, 0].legend(frameon=False, fontsize=8, loc="upper left")
    for ax in axes[:, 0]:
        ax.set_ylabel(ylab)
    fig.tight_layout()
    save(fig, name)
    if name == "Fig1_sdid_price":
        fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.2))
        for ax, s in zip(axes.flat, TREATED):
            r = cases[s]
            ax.hist(pct(r["placebos"].values), bins=14, color=GREY, edgecolor="white")
            ax.axvline(r["pct"], color=BLUE, lw=2)
            ax.set_title(f"{NAMES[s]}: p = {r['p']:.2f}", fontsize=9, loc="left")
            ax.set_xlabel("Placebo effect (%)")
        fig.tight_layout()
        save(fig, "FigS2_placebos")

# Fig 2: annual effects vs symmetric-reversal benchmarks
A = pd.read_csv(TAB / "R1_annual_effects.csv")
fig, axes = plt.subplots(2, 2, figsize=(8.6, 6.4), sharey=True)
for ax, s in zip(axes.flat, TREATED):
    d = A[A.state == s]
    ax.fill_between(d.year, d.band95_lo_pct, d.band95_hi_pct, color=GREY, alpha=.55, lw=0,
                    label="Donor placebo band (95%)")
    ax.axhline(0, color=MUTED, lw=.8)
    ax.axvline(TREATED[s] - .5, color=MUTED, lw=.8, ls=":")
    post = d[d.event_time >= 0]
    ax.plot(post.year, post.gn_reversal_pct, color=ORANGE, lw=2, ls="--", label="G&N full reversal, horizon-matched")
    if s == "OH":
        ax.fill_between(post.year, post.gn_scaled_low_pct, post.gn_scaled_high_pct, color=ORANGE, alpha=.18, lw=0,
                        label="G&N scaled by Ohio requirement cut")
    ax.plot(d.year, d.effect_pct, color=BLUE, lw=2, marker="o", ms=3.5, label="SDID annual effect")
    ax.set_title(NAMES[s], fontsize=9, loc="left")
    style(ax)
for ax in axes[:, 0]:
    ax.set_ylabel("Residential price effect (%)")
h, l = axes[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=2, frameon=False)
fig.tight_layout(rect=(0, .07, 1, 1))
save(fig, "Fig2_annual_effects_benchmarks")

# Fig 3: Ohio decomposition
D = pd.read_csv(TAB / "U5_ohio_decomposition.csv")
labels = {"state_average": "State average (all residential load)",
          "obligated": "Obligated utilities (IOUs + retail suppliers)",
          "exempt": "Exempt utilities (municipals + co-ops)",
          "within_difference": "Within-state difference (obligated - exempt)"}
fig, axes = plt.subplots(2, 2, figsize=(8.6, 6.4), sharey=True)
for ax, (k, lab) in zip(axes.flat, labels.items()):
    d = D[(D.series == k) & (D.year >= 2008)]
    ax.fill_between(d.year, -d.band95_pct, d.band95_pct, color=GREY, alpha=.55, lw=0, label="Donor placebo band (95%)")
    ax.axhline(0, color=MUTED, lw=.8)
    ax.axvline(2013.5, color=MUTED, lw=.8, ls=":")
    ax.plot(d.year, d.effect_pct, color=BLUE, lw=2, marker="o", ms=3.5, label="Ohio annual effect")
    ax.set_title(lab, fontsize=9, loc="left")
    ax.text(.02, .04, f"Average 2014-24: {d.avg_2014_24_pct.iloc[0]:+.1f}% (p = {d.p_avg.iloc[0]:.2f})",
            transform=ax.transAxes, fontsize=8, color=MUTED)
    style(ax)
for ax in axes[:, 0]:
    ax.set_ylabel("Price effect (%)")
h, l = axes[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=2, frameon=False)
fig.tight_layout(rect=(0, .06, 1, 1))
save(fig, "Fig3_ohio_decomposition")

# Fig S3: adoption event study (feasibility check)
E = pd.read_csv(TAB / "A1_adoption_event_study.csv")
fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6), sharey=True)
for ax, (k, lab) in zip(axes, [("within_gap", "Within-state gap: obligated - exempt"),
                               ("state_price", "State average residential price")]):
    d = E[E.outcome == k]
    ax.fill_between(d.event_time, d.lo95_pct, d.hi95_pct, color=GREY, alpha=.6, lw=0, label="95% percentile interval (state-cluster bootstrap)")
    ax.axhline(0, color=MUTED, lw=.8)
    ax.axvline(-.5, color=MUTED, lw=.8, ls=":")
    ax.plot(d.event_time, d.att_pct, color=BLUE, lw=2, marker="o", ms=3.5, label="ATT(e), 11 cohorts vs 15 states without a mandatory RPS")
    ax.set_title(lab, fontsize=9, loc="left")
    ax.set_xlabel("Years since first RPS compliance year")
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    style(ax)
axes[0].set_ylabel("Effect relative to year -1 (%)")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=2, frameon=False)
fig.tight_layout(rect=(0, .1, 1, 1))
save(fig, "FigS3_adoption_event_study")
print("figures written to", FIG)
