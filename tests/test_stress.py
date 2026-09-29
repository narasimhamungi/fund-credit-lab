import pandas as pd
import pytest

from fundcreditlab.config import DEFAULT_LIMITS
from fundcreditlab.loader import load_nmfp_zip
from fundcreditlab.metrics import series_metrics
from fundcreditlab.stress import worst_outflow


def test_worst_outflow_rolling_window():
    net = pd.Series([10, -20, -30, -10, 5, -15], dtype=float)
    assert worst_outflow(net, 5) == 70          # last five days: -20-30-10+5-15
    assert worst_outflow(net, 2) == 50          # -20-30
    assert worst_outflow(pd.Series([5.0, 5.0]), 5) == 0.0   # never an outflow


def test_worst_outflow_short_series_uses_available_days():
    assert worst_outflow(pd.Series([-3.0, -4.0]), 5) == 7


def test_stress_coverage_for_alpha(nmfp_zip):
    alpha = {m["series_id"]: m for m in series_metrics(load_nmfp_zip(nmfp_zip))}["S000000001"]
    s = alpha["stress"]
    assert s["worst_outflow"] == pytest.approx(70e6)
    assert s["worst_outflow_pct_of_assets"] == pytest.approx(7.0)
    assert s["weekly_coverage_of_worst_outflow"] == pytest.approx(600e6 / 70e6)
    by_level = {x["shock_pct"]: x for x in s["shocks"]}
    assert by_level[20.0]["covered_by_daily"] is True      # $200m vs $380m daily liquid
    assert by_level[40.0]["covered_by_daily"] is False     # $400m vs $380m
    assert by_level[40.0]["covered_by_weekly"] is True     # $400m vs $600m weekly


def test_no_flow_data_leaves_historical_stress_empty(nmfp_zip):
    gamma = {m["series_id"]: m for m in series_metrics(load_nmfp_zip(nmfp_zip))}["S000000002"]
    assert gamma["stress"]["worst_outflow"] is None
    assert gamma["stress"]["weekly_coverage_of_worst_outflow"] is None
    assert len(gamma["stress"]["shocks"]) == len(DEFAULT_LIMITS.shock_levels_pct)
