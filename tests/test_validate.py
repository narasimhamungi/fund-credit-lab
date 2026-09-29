from fundcreditlab.loader import latest_submissions, load_nmfp_zip
from fundcreditlab.validate import validate


def _findings(nmfp_zip):
    t = load_nmfp_zip(nmfp_zip)
    return validate(t, latest_submissions(t["SUBMISSION"]))


def test_bad_series_is_flagged_on_every_check(nmfp_zip):
    checks = {f.check for f in _findings(nmfp_zip) if f.accession == "0004-26-000001"}
    assert {"wal_lt_wam", "holdings_total", "matured_holding", "wla_lt_dla"} <= checks


def test_clean_series_has_no_findings(nmfp_zip):
    fs = _findings(nmfp_zip)
    for acc in ("0001-26-000002", "0002-26-000001", "0003-26-000001"):
        assert [f for f in fs if f.accession == acc] == []


def test_superseded_filing_is_not_validated(nmfp_zip):
    assert not [f for f in _findings(nmfp_zip) if f.accession == "0001-26-000001"]
