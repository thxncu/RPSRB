"""23 - Same-sample adoption check: event study of RPS adoption.

Callaway-Sant'Anna-style ATT(e) with base year g-1 for 11 adoption cohorts; controls are the 15 states
without a mandatory RPS (never-RPS and voluntary-goal states; config.NEVER_RPS_CONTROLS).
Outcomes: within-state gap D = log(obligated price) - log(exempt price), and the state average price.
Inference: 999 state-cluster bootstrap draws (treated and control states resampled separately).

Tables
  A1_adoption_event_study   ATT(e), bootstrap SE and 95% interval, mean requirement, cohorts per e
  A2_adoption_split         restructured vs non-restructured cohorts (499 draws)
"""
import numpy as np
import pandas as pd

from rpsrb.config import (DER, SEED, ADOPTION_COHORTS as COH, ADOPTION_CENSOR as CENSOR,
                          NEVER_RPS_CONTROLS as CTRL, RESTRUCTURED)
from rpsrb.data import within_panel, wide, save

W = within_panel()
W = W[W.year >= 2000]
REQ = pd.read_csv(DER / "rps_requirements_pct.csv", index_col="year")
OUT = {"within_gap": np.log(W.pivot(index="year", columns="state", values="p_obl"))
                     - np.log(W.pivot(index="year", columns="state", values="p_exm")),
       "state_price": wide("residential_price").loc[2000:]}
E = range(-6, 13)


def valid(s, e):
    t = COH[s] + e
    return 2000 <= t <= 2024 and COH[s] - 1 >= 2000 and not (s in CENSOR and t >= CENSOR[s])


def att(Y, coh, ctrl):
    out = {}
    for e in E:
        if e == -1:
            out[e] = 0.0
            continue
        v = [(Y.at[COH[s] + e, s] - Y.at[COH[s] - 1, s])
             - np.nanmean((Y.loc[COH[s] + e, ctrl] - Y.loc[COH[s] - 1, ctrl]).values)
             for s in coh if valid(s, e)]
        out[e] = np.mean(v) if v else np.nan
    return pd.Series(out).sort_index()


def boot(Y, coh, reps, rng):
    return pd.concat([att(Y, list(rng.choice(coh, len(coh))), list(rng.choice(CTRL, len(CTRL))))
                      for _ in range(reps)], axis=1)


rng = np.random.default_rng(SEED)
coh = list(COH)
rows = []
for lab, Y in OUT.items():
    est, bs = att(Y, coh, CTRL), boot(Y, coh, 999, rng)
    for e in E:
        rows.append({"outcome": lab, "event_time": e, "att_pct": 100 * est[e], "se_pct": 100 * bs.loc[e].std(),
                     "lo95_pct": 100 * bs.loc[e].quantile(.025), "hi95_pct": 100 * bs.loc[e].quantile(.975),
                     "mean_requirement_pct": np.mean([REQ.at[COH[s] + e, s] for s in coh if valid(s, e)]) if e >= 0 else 0.0,
                     "n_cohorts": sum(valid(s, e) for s in coh)})
A1 = save(pd.DataFrame(rows), "A1_adoption_event_study")
print(A1.pivot(index="event_time", columns="outcome", values="att_pct").round(1).T.to_string())

rows = []
for grp, cs in [("restructured", RESTRUCTURED), ("non-restructured", [s for s in coh if s not in RESTRUCTURED])]:
    for lab, Y in OUT.items():
        est, bs = att(Y, cs, CTRL), boot(Y, cs, 499, rng)
        for e in E:
            rows.append({"cohorts": grp, "outcome": lab, "event_time": e, "att_pct": 100 * est[e],
                         "se_pct": 100 * bs.loc[e].std()})
save(pd.DataFrame(rows), "A2_adoption_split")
