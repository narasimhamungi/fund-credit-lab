import pandas as pd

from fundcreditlab.cli import main
from fundcreditlab.loader import latest_submissions, load_nmfp_zip
from fundcreditlab.metrics import series_metrics
from fundcreditlab.report import render_memo
from fundcreditlab.validate import validate


def test_memo_states_it_is_not_a_rating_and_lists_flags(nmfp_zip):
    t = load_nmfp_zip(nmfp_zip)
    ms = {m["series_id"]: m for m in series_metrics(t)}
    memo = render_memo(ms["S000000002"], validate(t, latest_submissions(t["SUBMISSION"])))
    assert "Not a credit rating" in memo
    assert "thin WAM headroom" in memo and "FINCO Z" in memo
    assert "Fitch" not in memo.split("Not a credit rating")[0]  # no agency branding in the header


def test_memo_includes_data_quality_section_only_when_findings_exist(nmfp_zip):
    t = load_nmfp_zip(nmfp_zip)
    fs = validate(t, latest_submissions(t["SUBMISSION"]))
    ms = {m["series_id"]: m for m in series_metrics(t)}
    assert "Data-quality findings" in render_memo(ms["S000000004"], fs)
    assert "Data-quality findings" not in render_memo(ms["S000000001"], fs)


def test_cli_writes_summary_and_memos(nmfp_zip, tmp_path, capsys):
    out = tmp_path / "out"
    assert main(["analyze", "--zip", str(nmfp_zip), "--out", str(out)]) == 0
    summary = pd.read_csv(out / "summary.csv")
    assert set(summary["series_id"]) == {"S000000001", "S000000002", "S000000003", "S000000004"}
    assert len(list((out / "memos").glob("*.md"))) == 4
    assert "4 series analysed" in capsys.readouterr().out


def test_cli_series_filter(nmfp_zip, tmp_path):
    out = tmp_path / "out"
    main(["analyze", "--zip", str(nmfp_zip), "--out", str(out), "--series", "S000000001"])
    assert list(pd.read_csv(out / "summary.csv")["series_id"]) == ["S000000001"]
