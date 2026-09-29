import zipfile

import pandas as pd
import pytest

from conftest import build_tables, write_zip
from fundcreditlab.loader import NmfpLoadError, latest_submissions, load_nmfp_zip


def test_loads_all_tables_and_coerces_types(nmfp_zip):
    t = load_nmfp_zip(nmfp_zip)
    assert set(t) >= {"SUBMISSION", "SERIESLEVELINFO", "SCHPORTFOLIOSECURITIES", "NRSRO", "_UNPARSED", "_META"}
    assert pd.api.types.is_numeric_dtype(t["SERIESLEVELINFO"]["AVERAGEPORTFOLIOMATURITY"])
    assert pd.api.types.is_datetime64_any_dtype(t["SUBMISSION"]["REPORTDATE"])


def test_live_member_names_carry_nmfp_prefix(nmfp_zip):
    # Regression: the live ZIP names members NMFP_<TABLE>.tsv; bare-name matching failed on it.
    assert "NMFP_SUBMISSION.tsv" in zipfile.ZipFile(nmfp_zip).namelist()
    assert not load_nmfp_zip(nmfp_zip)["SUBMISSION"].empty


def test_sec_date_format_is_parsed(nmfp_zip):
    # Regression: live dates are DD-MON-YYYY (e.g. 31-JAN-2026).
    raw = pd.read_csv(zipfile.ZipFile(nmfp_zip).open("NMFP_SUBMISSION.tsv"), sep="\t", dtype=str)
    assert raw["REPORTDATE"].iloc[0] == "31-JAN-2026"
    t = load_nmfp_zip(nmfp_zip)
    assert (t["SUBMISSION"]["REPORTDATE"] == pd.Timestamp("2026-01-31")).all()


def test_fractional_percentages_are_converted_to_percent(nmfp_zip):
    # Regression: live percentages are fractions (0.81 = 81%).
    t = load_nmfp_zip(nmfp_zip)
    assert t["_META"]["pct_multiplier"].iloc[0] == 100.0
    sec = t["SCHPORTFOLIOSECURITIES"]
    tsy = sec[(sec["ACCESSION_NUMBER"] == "0001-26-000002") & (sec["NAMEOFISSUER"] == "US TREASURY")]
    assert tsy["PERCENTAGEOFMONEYMARKETFUNDNET"].iloc[0] == pytest.approx(81)


def test_legacy_layout_loads_to_the_same_numbers(nmfp_zip, legacy_zip):
    live, legacy = load_nmfp_zip(nmfp_zip), load_nmfp_zip(legacy_zip)
    assert legacy["_META"]["pct_multiplier"].iloc[0] == 1.0
    for table, col in (("SCHPORTFOLIOSECURITIES", "PERCENTAGEOFMONEYMARKETFUNDNET"),
                       ("LIQUIDASSETSDETAILS", "PCTWEEKLYLIQUIDASSETS"),
                       ("SUBMISSION", "REPORTDATE")):
        pd.testing.assert_series_equal(live[table][col], legacy[table][col], check_dtype=False)


def test_unknown_percentage_scale_raises(tmp_path):
    tables = build_tables()
    for r in tables["SCHPORTFOLIOSECURITIES"]:
        r["PERCENTAGEOFMONEYMARKETFUNDNET"] /= 10     # totals of about 10: neither fractions nor percent
    with pytest.raises(NmfpLoadError, match="percentage scale"):
        load_nmfp_zip(write_zip(tmp_path / "x.zip", tables=tables, live=False))


def test_unparsable_values_are_recorded_not_dropped(nmfp_zip):
    u = load_nmfp_zip(nmfp_zip)["_UNPARSED"]
    assert list(u[["ACCESSION_NUMBER", "COLUMN", "VALUE"]].itertuples(index=False, name=None)) == [
        ("0004-26-000001", "PCTDAILYLIQUIDASSETS", "n/a")]


def test_member_extension_does_not_matter(tmp_path):
    t = load_nmfp_zip(write_zip(tmp_path / "x.zip", extension=".txt"))
    assert not t["SERIESLEVELINFO"].empty


def test_missing_required_table_raises(tmp_path):
    p = write_zip(tmp_path / "x.zip", drop=("SERIESLEVELINFO",))
    with pytest.raises(NmfpLoadError, match="SERIESLEVELINFO"):
        load_nmfp_zip(p)


def test_missing_optional_table_is_empty_frame(tmp_path):
    t = load_nmfp_zip(write_zip(tmp_path / "x.zip", drop=("NRSRO",)))
    assert t["NRSRO"].empty


def test_missing_file_raises(tmp_path):
    with pytest.raises(NmfpLoadError, match="not found"):
        load_nmfp_zip(tmp_path / "nope.zip")


def test_amendment_supersedes_original_and_nt_notice_is_dropped(nmfp_zip):
    latest = latest_submissions(load_nmfp_zip(nmfp_zip)["SUBMISSION"])
    alpha = latest[latest["SERIESID"] == "S000000001"]
    assert list(alpha["ACCESSION_NUMBER"]) == ["0001-26-000002"]
    assert not latest["SUBMISSIONTYPE"].str.startswith("NT").any()
    assert len(latest) == 6
