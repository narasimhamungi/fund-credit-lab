import pytest

from fundcreditlab.loader import load_nmfp_zip
from fundcreditlab.metrics import series_metrics


@pytest.fixture
def by_id(nmfp_zip):
    return {m["series_id"]: m for m in series_metrics(load_nmfp_zip(nmfp_zip))}


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
    flags = " | ".join(by_id["S000000002"]["flags"])
    for expected in ("thin WAM", "thin WAL", "thin DLA", "thin WLA", "FINCO Z"):
        assert expected in flags


def test_tax_exempt_category_skips_liquidity_tests(by_id):
    d = by_id["S000000003"]
    assert d["liquidity_tested"] is False
    assert d["headroom"]["dla_pp"] is None and d["headroom"]["wla_pp"] is None
    assert not any("DLA" in f or "WLA" in f for f in d["flags"])


def test_concentration_numbers(by_id):
    c = by_id["S000000001"]["concentration"]
    assert c["top1_issuer"] == "BANK X" and c["top1_pct"] == 8      # Treasuries excluded
    assert c["top5_pct"] == 14
    assert c["hhi"] == pytest.approx(0.08**2 + 0.06**2)


def test_government_only_portfolio_has_no_concentration(by_id):
    c = by_id["S000000002"]["concentration"]
    assert c["top1_issuer"] == "FINCO Z"      # the one non-government holding
    from fundcreditlab.metrics import issuer_concentration
    import pandas as pd
    gov = pd.DataFrame({"NAMEOFISSUER": ["US TREASURY"], "INVESTMENTCATEGORY": ["U.S. Treasury Debt"],
                        "PERCENTAGEOFMONEYMARKETFUNDNET": [100.0]})
    assert issuer_concentration(gov)["top1_issuer"] is None


def test_category_mix_sorted_and_summed(by_id):
    mix = by_id["S000000001"]["category_mix"]
    assert list(mix)[0] == "U.S. Treasury Debt"
    assert sum(mix.values()) == pytest.approx(100)


def test_rating_coverage_counts_security_ratings_only(by_id):
    rc = by_id["S000000001"]["rating_coverage"]
    assert rc["securities"] == 3
    assert rc["rated_share"] == pytest.approx(2 / 3)   # guarantor rating does not count
    assert rc["by_agency"]["Fitch"] == pytest.approx(1 / 3)  # security-level only
    assert set(rc["by_agency"]) == {"S&P", "Fitch", "Moody's"}


def test_explicit_report_date_filter(nmfp_zip):
    t = load_nmfp_zip(nmfp_zip)
    assert len(series_metrics(t, "2026-01-31")) == 4
    assert series_metrics(t, "2025-12-31") == []
