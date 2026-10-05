"""Benchmark savings implied by reversing adoption-side estimates, and one-sided tests against them.

Adoption estimates are price increases. If adoption raised prices by X percent, full reversal lowers the
price by X/(1+X) percent, i.e. by log(1+X) in log points. All averaging over years is done in log points,
because the SDID estimate is the average log gap. Benchmarks are returned as negative percent changes
(savings). Compliance-cost benchmarks are shares of the bill, so removing a cost share s lowers the price
by s percent (log(1-s)).
"""
import numpy as np
from scipy.stats import norm

from .config import GN_PATH, GN_PER_PP, OH_CUT, LBNL_AVG

_K = list(GN_PATH)
_V = [np.log1p(v / 100) for v in GN_PATH.values()]


def gn_log(k):
    """Greenstone-Nath log price increase k years after adoption (linear in log points between 0, 7, 12)."""
    return float(np.interp(k, _K, _V))


def rev_pct(log_increase):
    """Saving (negative percent) from reversing a log price increase."""
    return 100.0 * (np.exp(-log_increase) - 1.0)


def lp(b_pct):
    """Percent change -> log points."""
    return np.log1p(b_pct / 100.0)


def scale_pct(b_pct, c):
    """Scale a benchmark by coverage share c in log points."""
    return 100.0 * (np.exp(c * lp(b_pct)) - 1.0)


def scaled_log(per_pp, year):
    return np.log1p(per_pp * OH_CUT[year] / 100.0)


def benchmarks(state, onset, end=2024):
    yrs = range(onset, end + 1)
    b = {"lbnl_avg": -LBNL_AVG,
         "gn_horizon_matched": rev_pct(np.mean([gn_log(y - onset) for y in yrs]))}
    if state == "OH":
        b["gn_scaled_low"] = rev_pct(np.mean([scaled_log(GN_PER_PP[0], y) for y in yrs]))
        b["gn_scaled_high"] = rev_pct(np.mean([scaled_log(GN_PER_PP[1], y) for y in yrs]))
    return b


def one_sided_p(tau, se, bench_pct):
    """H0: effect <= bench (savings at least |bench|); normal approximation with placebo SE."""
    return 1 - norm.cdf((tau - lp(bench_pct)) / se)


def rank_p(tau, placebos, bench_pct):
    """Permutation analogue: share of placebo estimates, shifted to the benchmark, at least as large as tau."""
    pl = np.asarray(placebos)
    return (1 + np.sum(pl + lp(bench_pct) >= tau)) / (1 + len(pl))
