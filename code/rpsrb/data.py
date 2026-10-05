"""Loaders for derived datasets (built by scripts 01-03) and small output helpers."""
import numpy as np
import pandas as pd

from .config import DER, TAB


def state_panel():
    return pd.read_csv(DER / "state_panel.csv")


def wide(col, log=True, panel=None):
    p = state_panel() if panel is None else panel
    m = p.pivot(index="year", columns="state", values=col)
    return np.log(m) if log else m


def henry_hub():
    return pd.read_csv(DER / "henry_hub_annual.csv", index_col="year")["hh_usd_mmbtu"]


def generation_shares():
    g = pd.read_csv(DER / "generation_shares.csv")
    return {c: g.pivot(index="year", columns="state", values=c)
            for c in ["re_share_pct", "gas_share_pct", "coal_share_pct"]}


def income():
    return pd.read_csv(DER / "median_income.csv").pivot(index="year", columns="state",
                                                        values="median_income")


def utility_panel():
    return pd.read_csv(DER / "utility_residential.csv")


def within_panel():
    return pd.read_csv(DER / "within_state_prices.csv")


def save(df, name, index=False):
    df.to_csv(TAB / f"{name}.csv", index=index)
    return df
