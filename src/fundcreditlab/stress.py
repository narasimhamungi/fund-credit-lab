"""Liquidity stress from reported shareholder flows and liquid-asset balances."""
from __future__ import annotations

import pandas as pd

from .config import Limits


def daily_net_flows(flows: pd.DataFrame, accession: str) -> pd.Series:
    """Series-level net flow (subscriptions minus redemptions) per date, all classes summed."""
    if flows.empty:
        return pd.Series(dtype=float)
    f = flows[flows["ACCESSION_NUMBER"] == accession]
    if f.empty:
        return pd.Series(dtype=float)
    f = f.dropna(subset=["DAILYSHAREHOLDERFLOWDATE"])
    net = (f["DAILYGROSSSUBSCRIPTIONS"].fillna(0) - f["DAILYGROSSREDEMPTIONS"].fillna(0))
    return net.groupby(f["DAILYSHAREHOLDERFLOWDATE"]).sum().sort_index()


def worst_outflow(net: pd.Series, window: int) -> float:
    """Largest cumulative net outflow (positive number, dollars) over any `window`
    consecutive reported days. 0.0 if there was never a net outflow."""
    if net.empty:
        return 0.0
    rolled = net.rolling(window=min(window, len(net)), min_periods=min(window, len(net))).sum()
    return float(max(0.0, -rolled.min()))


def stress_table(net_assets: float, wla_value: float | None, dla_value: float | None,
                 flows_worst: float | None, limits: Limits) -> dict:
    """Instantaneous-shock coverage plus historical-flow coverage."""
    shocks = []
    for lvl in limits.shock_levels_pct:
        need = net_assets * lvl / 100.0
        shocks.append({
            "shock_pct": lvl,
            "amount": need,
            "covered_by_daily": None if dla_value is None else dla_value >= need,
            "covered_by_weekly": None if wla_value is None else wla_value >= need,
        })
    out = {"shocks": shocks, "worst_outflow": flows_worst, "worst_outflow_pct_of_assets": None,
           "weekly_coverage_of_worst_outflow": None}
    if flows_worst is not None and net_assets:
        out["worst_outflow_pct_of_assets"] = flows_worst / net_assets * 100.0
        if flows_worst > 0 and wla_value is not None:
            out["weekly_coverage_of_worst_outflow"] = wla_value / flows_worst
    return out
