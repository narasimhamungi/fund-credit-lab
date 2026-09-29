import pandas as pd
import pytest

from conftest import write_zip
from fundcreditlab.loader import NmfpLoadError, latest_submissions, load_nmfp_zip


def test_loads_all_tables_and_coerces_types(nmfp_zip):
    t = load_nmfp_zip(nmfp_zip)
    assert set(t) >= {"SUBMISSION", "SERIESLEVELINFO", "SCHPORTFOLIOSECURITIES", "NRSRO"}
    assert pd.api.types.is_numeric_dtype(t["SERIESLEVELINFO"]["AVERAGEPORTFOLIOMATURITY"])
    assert pd.api.types.is_datetime64_any_dtype(t["SUBMISSION"]["REPORTDATE"])


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
    assert len(latest) == 4
