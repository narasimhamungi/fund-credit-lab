import pandas as pd

from fundcreditlab.cli import main
from fundcreditlab.loader import latest_submissions, load_nmfp_zip
from fundcreditlab.metrics import series_metrics
from fundcreditlab.report import render_memo
from fundcreditlab.validate import validate


def _memos(nmfp_zip):
    t = load_nmfp_zip(nmfp_zip)
    fs = validate(t, latest_submissions(t["SUBMISSION"]))
    return {m["series_id"]: render_memo(m, fs) for m in series_metrics(t)}


def test_memo_states_it_is_not_a_rating_and_lists_flags(nmfp_zip):
    memo = _memos(nmfp_zip)["S000000002"]
    assert "Not a credit rating" in memo
    assert "thin WAM headroom" in memo and "FINCO Z" in memo
    assert "largest counterparty DEALER A at 30.0%" in memo
    assert "Fitch" not in memo.split("Not a credit rating")[0]  # no agency branding in the header


def test_memo_states_when_no_ratings_are_reported(nmfp_zip):
    # Regression: the rating line was silently omitted when a filing carried no NRSRO rows.
    assert "no NRSRO ratings reported in this filing" in _memos(nmfp_zip)["S000000002"]
    assert "Rating coverage (as filed):** 60% of 5 securities, 14.0% of net assets" in _memos(nmfp_zip)["S000000001"]


def test_tax_exempt_memo_says_daily_minimum_does_not_apply(nmfp_zip):
    memo = _memos(nmfp_zip)["S000000003"]
    assert "does not apply to tax-exempt funds" in memo and "not applicable (tax-exempt)" in memo


def test_memo_includes_data_quality_section_only_when_findings_exist(nmfp_zip):
    memos = _memos(nmfp_zip)
    assert "Data-quality findings" in memos["S000000004"]
    assert "Data-quality findings" not in memos["S000000001"]


def test_cli_writes_outputs_and_leaves_out_feeders_by_default(nmfp_zip, tmp_path, capsys):
    out = tmp_path / "out"
    assert main(["analyze", "--zip", str(nmfp_zip), "--out", str(out)]) == 0
    summary = pd.read_csv(out / "summary.csv")
    assert set(summary["series_id"]) == {"S000000001", "S000000002", "S000000003", "S000000004", "S000000005"}
    assert len(list((out / "memos").glob("*.md"))) == 5
    findings = pd.read_csv(out / "findings.csv")
    assert set(findings["series_id"]) == {"S000000004"}
    printed = capsys.readouterr().out
    assert "5 series analysed" in printed and "1 feeder funds left out" in printed


def test_cli_include_feeders(nmfp_zip, tmp_path):
    out = tmp_path / "out"
    main(["analyze", "--zip", str(nmfp_zip), "--out", str(out), "--include-feeders"])
    assert "S000000006" in set(pd.read_csv(out / "summary.csv")["series_id"])


def test_cli_series_filter(nmfp_zip, tmp_path):
    out = tmp_path / "out"
    main(["analyze", "--zip", str(nmfp_zip), "--out", str(out), "--series", "S000000001"])
    assert list(pd.read_csv(out / "summary.csv")["series_id"]) == ["S000000001"]
