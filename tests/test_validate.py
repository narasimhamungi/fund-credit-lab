from conftest import build_tables, write_zip
from fundcreditlab.loader import latest_submissions, load_nmfp_zip
from fundcreditlab.validate import validate


def _findings(zip_path):
    t = load_nmfp_zip(zip_path)
    return validate(t, latest_submissions(t["SUBMISSION"]))


def test_bad_series_is_flagged_on_every_check(nmfp_zip):
    checks = {f.check for f in _findings(nmfp_zip) if f.accession == "0004-26-000001"}
    assert {"wal_lt_wam", "holdings_total", "matured_holding", "wla_lt_dla", "unparsed_value"} <= checks


def test_clean_series_have_no_findings(nmfp_zip):
    fs = _findings(nmfp_zip)
    for acc in ("0001-26-000002", "0002-26-000001", "0003-26-000001", "0006-26-000001", "0007-26-000001"):
        assert [f for f in fs if f.accession == acc] == []


def test_superseded_filing_is_not_validated(nmfp_zip):
    assert not [f for f in _findings(nmfp_zip) if f.accession == "0001-26-000001"]


def test_rounding_above_100_percent_is_tolerated_but_real_excess_is_not(tmp_path):
    # Live data contains 100.01% (filed to 0.01pp); only values beyond the tolerance are findings.
    for value, flagged in ((100.01, False), (101.0, True)):
        tables = build_tables()
        tables["LIQUIDASSETSDETAILS"][0]["PCTWEEKLYLIQUIDASSETS"] = value
        fs = _findings(write_zip(tmp_path / f"x{value}.zip", tables=tables))
        hit = [f for f in fs if f.accession == "0001-26-000002" and f.check == "pct_out_of_range"]
        assert bool(hit) is flagged
