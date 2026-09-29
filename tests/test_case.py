import pandas as pd
import pytest

from conftest import write_zip
from fundcreditlab.case import build_case, rating_scale
from fundcreditlab.cli import main
from fundcreditlab.loader import load_nmfp_zip, read_table

FILES = ("liquidity_daily.csv", "flows_daily.csv", "top_entities.csv", "repo_counterparties.csv",
         "repo_collateral.csv", "ratings_by_agency.csv", "peer_stats.csv", "case_summary.md")


@pytest.fixture
def alpha(nmfp_zip):
    return build_case(nmfp_zip, load_nmfp_zip(nmfp_zip), "S000000001", peers=["S000000004"])


def test_cli_writes_every_case_file(nmfp_zip, tmp_path, capsys):
    assert main(["case", "--zip", str(nmfp_zip), "--series", "S000000001", "--peer", "S000000004",
                 "--out", str(tmp_path)]) == 0
    d = tmp_path / "case_S000000001"
    assert all((d / f).exists() for f in FILES)
    summary = (d / "case_summary.md").read_text(encoding="utf-8")
    assert "Not a credit rating" in summary and "Alpha Prime Fund" in summary
    assert "case extract for S000000001" in capsys.readouterr().out


def test_unknown_series_is_an_error(nmfp_zip, tmp_path):
    assert main(["case", "--zip", str(nmfp_zip), "--series", "S999999999", "--out", str(tmp_path)]) == 2


def test_top_entities_use_legal_entity_grouping(alpha):
    top = alpha["top_entities"]
    assert top.iloc[0]["entity"] == "BANK X" and top.iloc[0]["pct_of_net_assets"] == pytest.approx(8)


def test_repo_counterparty_collateral_cover(alpha):
    rp = alpha["repo_counterparties"].set_index("counterparty")
    assert rp.loc["DEALER C", "other_collateral_pct"] == pytest.approx(5)
    assert rp.loc["DEALER C", "collateral_to_position"] == pytest.approx(55 / 50)   # $55m collateral, $50m repo


def test_repo_collateral_mix(alpha):
    rc = alpha["repo_collateral"]
    mix = dict(zip(rc["collateral_category"], rc["share_of_repo_type_pct"]))
    assert mix["Equity"] == pytest.approx(30 / 55 * 100) and mix["Corporate Debt Securities"] == pytest.approx(25 / 55 * 100)
    assert set(rc["repo_type"]) == {"other_repo"}


def test_ratings_by_agency_split_by_scale_and_exclude_placeholders(alpha):
    ra = alpha["ratings_by_agency"]
    got = {(r.agency, r.scale, r.rating): r.pct_of_net_assets for r in ra.itertuples()}
    assert got[("S&P", "short-term", "A-1+")] == pytest.approx(5)
    assert got[("Fitch", "short-term", "F1+")] == pytest.approx(5)
    assert got[("Fitch", "long-term/other", "AA")] == pytest.approx(5)
    assert got[("Moody's", "short-term", "P-1")] == pytest.approx(6)
    assert not any(k[2] == "N/A" for k in got)


def test_peer_stats_rank_the_fund_within_its_category(alpha):
    ps = alpha["peer_stats"].set_index("metric")
    wla = ps.loc["wla_min_pct"]
    assert wla["peers"] == 2 and wla["median"] == pytest.approx(40)       # Alpha 60, Epsilon 20; Eta is a feeder
    assert wla["fund_percentile"] == pytest.approx(100)


def test_liquidity_daily_includes_peers(alpha):
    liq = alpha["liquidity_daily"]
    assert liq.groupby("series_id").size().to_dict() == {"S000000001": 2, "S000000004": 2}


def test_government_repo_collateral_is_labelled(nmfp_zip):
    gamma = build_case(nmfp_zip, load_nmfp_zip(nmfp_zip), "S000000002")
    rc = gamma["repo_collateral"]
    assert set(rc["repo_type"]) == {"government_repo"}
    assert gamma["repo_counterparties"].set_index("counterparty").loc["DEALER A", "collateral_to_position"] == pytest.approx(1.02)


def test_read_table_filters_accessions_and_tolerates_absence(nmfp_zip, tmp_path):
    assert len(read_table(nmfp_zip, "COLLATERALISSUERS", {"0002-26-000001"})) == 2
    no_coll = write_zip(tmp_path / "x.zip", drop=("COLLATERALISSUERS",))
    assert read_table(no_coll, "COLLATERALISSUERS", {"x"}).empty
    c = build_case(no_coll, load_nmfp_zip(no_coll), "S000000001")
    assert c["repo_collateral"].empty and c["collateral_rows"] == 0


@pytest.mark.parametrize("code,scale", [("A-1+", "short-term"), ("P-1", "short-term"), ("F1+", "short-term"),
                                        ("VMIG 1", "short-term"), ("AA", "long-term/other"), ("Aa2", "long-term/other"),
                                        (None, "long-term/other")])
def test_rating_scale(code, scale):
    assert rating_scale(code) == scale
