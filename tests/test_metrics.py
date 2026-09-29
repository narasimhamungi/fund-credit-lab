import pandas as pd
import pytest

from conftest import AGY_REPO, OTHER_REPO, TSY_REPO
from fundcreditlab.loader import load_nmfp_zip
from fundcreditlab.metrics import holding_bucket, issuer_concentration, series_metrics


@pytest.fixture
def by_id(nmfp_zip):
    return {m["series_id"]: m for m in series_metrics(load_nmfp_zip(nmfp_zip))}


def _flags(m):
    return " | ".join(m["flags"])


def test_uses_amended_filing_values(by_id):
    a = by_id["S000000001"]
    assert a["accession"] == "0001-26-000002"
    assert a["wam"] == 30 and a["wal"] == 70


def test_headroom_to_limits(by_id):
    h = by_id["S000000001"]["headroom"]
    assert h["wam_days"] == 30 and h["wal_days"] == 50
    assert h["dla_pp"] == pytest.approx(13)   # lowest DLA 38% vs 25% minimum
    assert h["wla_pp"] == pytest.approx(10)   # lowest WLA 60% vs 50% minimum
    assert by_id["S000000001"]["flags"] == []


def test_thin_headroom_and_concentration_flags(by_id):
    flags = _flags(by_id["S000000002"])
    for expected in ("thin WAM", "thin WAL", "thin DLA", "thin WLA", "FINCO Z"):
        assert expected in flags


def test_tax_exempt_fund_skips_daily_but_not_weekly_minimum(by_id):
    # Regression: rule 2a-7(d)(4)(ii) exempts tax-exempt funds from the daily minimum only.
    d = by_id["S000000003"]
    assert d["dla_tested"] is False and d["headroom"]["dla_pp"] is None
    assert d["headroom"]["wla_pp"] == pytest.approx(-20)
    assert "WLA fell to 30.0% on 2026-01-30, below the 50% acquisition minimum" in _flags(d)
    assert "DLA" not in _flags(d)


def test_single_state_fund_is_tax_exempt(by_id):
    # Regression: 'Single State' funds were tested against the daily minimum.
    z = by_id["S000000005"]
    assert z["dla_tested"] is False and z["dla_min_pct"] == pytest.approx(3)
    assert "DLA" not in _flags(z) and "WLA" not in _flags(z)
    assert z["headroom"]["wla_pp"] == pytest.approx(10)


def test_board_notification_threshold_is_flagged(by_id):
    assert "WLA fell to 20.0% on 2026-01-30, below the 25% board-notification threshold" in _flags(by_id["S000000004"])


def test_other_repo_is_not_classified_as_government():
    # Regression: the 'treasury' keyword matched 'Other Repurchase Agreement ... outside Treasury'.
    assert holding_bucket(OTHER_REPO) == "other_repo"
    assert holding_bucket(TSY_REPO) == "government_repo"
    assert holding_bucket(AGY_REPO) == "government_repo"
    assert holding_bucket("U.S. Treasury Debt") == "government"
    assert holding_bucket("U.S. Government Agency Debt (if categorized as no-coupon discount notes)") == "government"
    assert holding_bucket("Non-U.S. Sovereign, Sub-Sovereign and Supra-National debt") == "credit"
    assert holding_bucket(None) == "credit"


def test_concentration_groups_by_lei_and_includes_other_repo(by_id):
    c = by_id["S000000001"]["concentration"]
    assert c["top1_issuer"] == "BANK X" and c["top1_pct"] == pytest.approx(8)   # 5% + 3% under one LEI
    assert c["top5_pct"] == pytest.approx(19)                                   # 8 + 6 + DEALER C 5
    assert c["hhi"] == pytest.approx(0.08**2 + 0.06**2 + 0.05**2)


def test_government_repo_is_reported_as_repo_not_credit_concentration(by_id):
    g = by_id["S000000002"]
    assert g["concentration"]["top1_issuer"] == "FINCO Z"
    r = g["repo"]
    assert r["repo_pct"] == pytest.approx(40) and r["gov_collateral_pct"] == pytest.approx(40)
    assert r["other_collateral_pct"] == 0 and r["counterparties"] == 2
    assert r["top_counterparty"] == "DEALER A" and r["top_counterparty_pct"] == pytest.approx(30)


def test_government_only_portfolio_has_no_concentration():
    gov = pd.DataFrame({"NAMEOFISSUER": ["US TREASURY", "DEALER A"], "INVESTMENTCATEGORY": ["U.S. Treasury Debt", TSY_REPO],
                        "PERCENTAGEOFMONEYMARKETFUNDNET": [60.0, 40.0]})
    assert issuer_concentration(gov)["top1_issuer"] is None


def test_feeder_is_marked_and_not_flagged_for_concentration(by_id):
    e = by_id["S000000006"]
    assert e["feeder"] is True and e["concentration"]["top1_pct"] == pytest.approx(100)
    assert "feeder fund" in _flags(e) and "issuer concentration" not in _flags(e)


def test_category_mix_sorted_and_summed(by_id):
    mix = by_id["S000000001"]["category_mix"]
    assert list(mix)[0] == "U.S. Treasury Debt"
    assert sum(mix.values()) == pytest.approx(100)


def test_rating_coverage_counts_security_ratings_only(by_id):
    rc = by_id["S000000001"]["rating_coverage"]
    assert rc["securities"] == 5
    assert rc["rated_share"] == pytest.approx(2 / 5)   # guarantor rating does not count
    assert rc["by_agency"]["Fitch"] == pytest.approx(1 / 5)
    assert set(rc["by_agency"]) == {"S&P", "Fitch", "Moody's"}


def test_explicit_report_date_filter(nmfp_zip):
    t = load_nmfp_zip(nmfp_zip)
    assert len(series_metrics(t, "2026-01-31")) == 6
    assert series_metrics(t, "2025-12-31") == []
