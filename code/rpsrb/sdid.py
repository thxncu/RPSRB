"""Synthetic difference-in-differences (Arkhangelsky et al., 2021) for a single treated unit,
with in-place placebo inference, annual effects, RMSPE-ratio and conformal tests.

Matrices are pandas DataFrames indexed by year with one column per state.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .config import EST_START


def pct(x):
    """Log points -> percent."""
    return 100.0 * (np.exp(x) - 1.0)


def _simplex_ls(A, b, zeta):
    """min_{c, w>=0, sum w = 1} ||c + A w - b||^2 + zeta^2 * len(b) * ||w||^2."""
    n = A.shape[1]
    x0 = np.concatenate([[b.mean() - A.mean()], np.full(n, 1.0 / n)])

    def obj(x):
        r = x[0] + A @ x[1:] - b
        return r @ r + zeta ** 2 * len(b) * (x[1:] @ x[1:])

    def grad(x):
        r = x[0] + A @ x[1:] - b
        return np.concatenate([[2 * r.sum()], 2 * (A.T @ r) + 2 * zeta ** 2 * len(b) * x[1:]])

    cons = [{"type": "eq", "fun": lambda x: x[1:].sum() - 1.0,
             "jac": lambda x: np.concatenate([[0.0], np.ones(n)])}]
    bnds = [(None, None)] + [(0.0, None)] * n
    res = minimize(obj, x0, jac=grad, bounds=bnds, constraints=cons, method="SLSQP",
                   options={"maxiter": 800, "ftol": 1e-12})
    if not res.success:
        res = minimize(obj, x0, jac=grad, bounds=bnds, constraints=cons, method="SLSQP",
                       options={"maxiter": 2000, "ftol": 1e-10})
    w = np.clip(res.x[1:], 0, None)
    return res.x[0], w / max(w.sum(), 1e-12)


def sdid_tau(Yc, yt, T0):
    """Yc: (N0, T) donor outcomes; yt: (T,) treated outcome; T0 pre-periods."""
    T1 = Yc.shape[1] - T0
    sigma = np.diff(Yc[:, :T0], axis=1).std(ddof=1)
    om0, om = _simplex_ls(Yc[:, :T0].T, yt[:T0], (T1 ** 0.25) * sigma)
    _, lam = _simplex_ls(Yc[:, :T0], Yc[:, T0:].mean(axis=1), 1e-6 * sigma)
    tau = (yt[T0:].mean() - yt[:T0] @ lam) - om @ (Yc[:, T0:].mean(axis=1) - Yc[:, :T0] @ lam)
    synth = om0 + om @ Yc
    gap = yt - synth
    return {"tau": tau, "omega": om, "lambda": lam, "synth": synth, "gap": gap,
            "annual": gap - gap[:T0] @ lam}      # mean of post 'annual' equals tau


def _prep(M, treated, onset, donors, end=None):
    yrs = [y for y in M.index if y >= EST_START and (end is None or y <= end)]
    sub = M.loc[yrs, [treated] + [d for d in donors if d != treated]].dropna(axis=1)
    dn = [c for c in sub.columns if c != treated]
    T0 = sum(y < onset for y in yrs)
    return np.array(yrs), sub[dn].T.values, sub[treated].values, T0, dn


def fit(M, treated, onset, donors, end=None):
    yrs, Yc, yt, T0, dn = _prep(M, treated, onset, donors, end)
    f = sdid_tau(Yc, yt, T0)
    f.update(years=yrs, T0=T0, donors=dn, y_treated=yt,
             omega=pd.Series(f["omega"], index=dn), lam=pd.Series(f["lambda"], index=yrs[:T0]))
    return f


def run_case(M, treated, onset, donors, end=None, keep_paths=False):
    """SDID estimate + in-place placebo inference (each donor treated in turn)."""
    f = fit(M, treated, onset, donors, end)
    dn = f["donors"]
    plac, paths = [], {}
    for d in dn:
        pf = fit(M, d, onset, [x for x in dn if x != d], end)
        plac.append(pf["tau"])
        if keep_paths:
            paths[d] = pf
    plac = np.array(plac)
    p = (1 + np.sum(np.abs(plac) >= abs(f["tau"]))) / (1 + len(plac))
    se = plac.std(ddof=1)
    f.update(placebos=pd.Series(plac, index=dn), se=se, p=p, pct=pct(f["tau"]),
             ci_lo=pct(f["tau"] - 1.96 * se), ci_hi=pct(f["tau"] + 1.96 * se),
             T1=len(f["years"]) - f["T0"], placebo_fits=paths)
    return f


def rmspe_ratio_test(case):
    """Abadie et al. (2010) post/pre RMSPE ratio inference using raw gaps; needs keep_paths=True."""
    def stats(f):
        g, T0 = f["gap"], f["T0"]
        pre = np.sqrt(np.mean(g[:T0] ** 2))
        return pre, np.sqrt(np.mean(g[T0:] ** 2)) / pre
    pre, ratio = stats(case)
    arr = np.array([stats(pf) for pf in case["placebo_fits"].values()])
    med = np.median(arr[:, 0])
    return {"pre_rmspe_pct": 100 * pre, "donor_median_pre_rmspe_pct": 100 * med,
            "pre_mspe_over_median": (pre / med) ** 2, "post_pre_ratio": ratio,
            "p_ratio": (1 + np.sum(arr[:, 1] >= ratio)) / (1 + len(arr))}


def conformal_p(M, treated, onset, donors, stat="abs_mean"):
    """Chernozhukov, Wuthrich & Zhu (2021) cyclic-shift test of the sharp null of no effect.
    Null-imposed SC fit (intercept, simplex weights, no ridge) on all periods.
    stat: 'abs_mean' (|mean post residual|), 'q1' (mean |residual|), 'q2' (RMS residual)."""
    yrs, Yc, yt, T0, dn = _prep(M, treated, onset, donors)
    c, w = _simplex_ls(Yc.T, yt, 0.0)
    u = yt - (c + w @ Yc)
    S = {"abs_mean": lambda e: abs(e[T0:].mean()),
         "q1": lambda e: np.mean(np.abs(e[T0:])),
         "q2": lambda e: np.sqrt(np.mean(e[T0:] ** 2))}[stat]
    s0 = S(u)
    return float(np.mean([S(np.roll(u, k)) >= s0 for k in range(len(u))]))


def sc_tau(Yc, yt, T0):
    """Classic synthetic control (Abadie et al., 2010): simplex weights, no intercept, no penalty,
    fitted to pre-period log outcomes; effect = mean post-period gap."""
    n = Yc.shape[0]
    A, b = Yc[:, :T0].T, yt[:T0]
    obj = lambda w: np.sum((A @ w - b) ** 2)
    grad = lambda w: 2 * A.T @ (A @ w - b)
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0, "jac": lambda w: np.ones(n)}]
    res = minimize(obj, np.full(n, 1.0 / n), jac=grad, bounds=[(0.0, None)] * n, constraints=cons,
                   method="SLSQP", options={"maxiter": 2000, "ftol": 1e-14})
    w = np.clip(res.x, 0, None)
    w = w / w.sum()
    gap = yt - w @ Yc
    return gap[T0:].mean(), w, gap


def run_sc(M, treated, onset, donors, end=None):
    """Classic SC estimate with in-place placebo p-value."""
    yrs, Yc, yt, T0, dn = _prep(M, treated, onset, donors, end)
    tau, w, gap = sc_tau(Yc, yt, T0)
    plac = []
    for i in range(len(dn)):
        others = np.delete(Yc, i, axis=0)
        plac.append(sc_tau(others, Yc[i], T0)[0])
    plac = np.array(plac)
    return {"tau": tau, "pct": pct(tau), "p": (1 + np.sum(np.abs(plac) >= abs(tau))) / (1 + len(plac)),
            "pre_rmspe_pct": 100 * np.sqrt(np.mean(gap[:T0] ** 2)), "weights": pd.Series(w, index=dn)}
