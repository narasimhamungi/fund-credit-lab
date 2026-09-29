"""Read the SEC Form N-MFP data set ZIP into pandas tables.

The data set is published by SEC DERA as tab-delimited text files, one per table
(SUBMISSION, SERIESLEVELINFO, ...). Member names are matched on the file stem, case-
insensitively, because the extension has varied. Download the ZIP yourself from
https://www.sec.gov/dera/data/form-nmfp-data-sets and pass its path in.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from .config import OPTIONAL_TABLES, REQUIRED_TABLES


class NmfpLoadError(RuntimeError):
    pass


def _stem(name: str) -> str:
    return Path(name).stem.upper()


def load_nmfp_zip(path: str | Path) -> dict[str, pd.DataFrame]:
    """Return {TABLE: DataFrame}. Raises NmfpLoadError if a required table is missing."""
    path = Path(path)
    if not path.exists():
        raise NmfpLoadError(f"file not found: {path}")
    tables: dict[str, pd.DataFrame] = {}
    with zipfile.ZipFile(path) as zf:
        members = {_stem(n): n for n in zf.namelist() if not n.endswith("/")}
        missing = [t for t in REQUIRED_TABLES if t not in members]
        if missing:
            raise NmfpLoadError(f"required table(s) missing from {path.name}: {missing}")
        for table in REQUIRED_TABLES + OPTIONAL_TABLES:
            if table in members:
                with zf.open(members[table]) as fh:
                    tables[table] = pd.read_csv(fh, sep="\t", dtype=str, keep_default_na=False,
                                                na_values=[""], encoding="utf-8")
            else:
                tables[table] = pd.DataFrame()
    return _coerce(tables)


_NUMERIC = {
    "SERIESLEVELINFO": ["AVERAGEPORTFOLIOMATURITY", "AVERAGELIFEMATURITY", "NETASSETOFSERIES"],
    "SCHPORTFOLIOSECURITIES": ["PERCENTAGEOFMONEYMARKETFUNDNET",
                               "INCLUDINGVALUEOFANYSPONSORSUPP", "EXCLUDINGVALUEOFANYSPONSORSUPP"],
    "LIQUIDASSETSDETAILS": ["TOTVALUEDAILYLIQUIDASSETS", "TOTVALUEWEEKLYLIQUIDASSETS",
                            "PCTDAILYLIQUIDASSETS", "PCTWEEKLYLIQUIDASSETS"],
    "DLYSHAREHOLDERFLOWREPORT": ["DAILYGROSSSUBSCRIPTIONS", "DAILYGROSSREDEMPTIONS"],
}
_DATES = {
    "SUBMISSION": ["FILING_DATE", "REPORTDATE"],
    "SCHPORTFOLIOSECURITIES": ["INVESTMENTMATURITYDATEWAM"],
    "LIQUIDASSETSDETAILS": ["TOTLIQUIDASSETSNEARPCTDATE"],
    "DLYSHAREHOLDERFLOWREPORT": ["DAILYSHAREHOLDERFLOWDATE"],
}


def _coerce(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    for name, cols in _NUMERIC.items():
        df = tables.get(name)
        if df is not None and not df.empty:
            for c in cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")
    for name, cols in _DATES.items():
        df = tables.get(name)
        if df is not None and not df.empty:
            for c in cols:
                if c in df.columns:
                    df[c] = pd.to_datetime(df[c], errors="coerce")
    return tables


def latest_submissions(submission: pd.DataFrame) -> pd.DataFrame:
    """One row per (SERIESID, REPORTDATE): the most recently filed version.

    Amendments (N-MFP/A etc.) supersede the original filing. 'NT' notices (inability
    to file on time) carry no data and are dropped.
    """
    df = submission.copy()
    df = df[~df["SUBMISSIONTYPE"].str.upper().str.startswith("NT")]
    df = df.sort_values(["SERIESID", "REPORTDATE", "FILING_DATE", "ACCESSION_NUMBER"])
    return df.groupby(["SERIESID", "REPORTDATE"], as_index=False).tail(1).reset_index(drop=True)
