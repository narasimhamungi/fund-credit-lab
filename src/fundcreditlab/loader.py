"""Read the SEC Form N-MFP data set ZIP into pandas tables.

Live layout (checked on the 20260810-20260908 data set): members are named
NMFP_<TABLE>.tsv, dates are DD-MON-YYYY, and percentage fields are fractions of 1
(0.4512 = 45.12%). Bare table names, ISO dates and 0-100 percentages are also accepted.
Download the ZIP from https://www.sec.gov/dera/data/form-nmfp-data-sets and pass its path.

Nothing is silently fixed: every value that cannot be parsed is recorded in the
"_UNPARSED" table and reported by validate.py.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from .config import MEMBER_PREFIX, OPTIONAL_TABLES, REQUIRED_TABLES


class NmfpLoadError(RuntimeError):
    pass


def _table_name(member: str) -> str:
    stem = Path(member).stem.upper()
    return stem[len(MEMBER_PREFIX):] if stem.startswith(MEMBER_PREFIX) else stem


def load_nmfp_zip(path: str | Path) -> dict[str, pd.DataFrame]:
    """Return {TABLE: DataFrame} plus "_UNPARSED" and "_META".

    Raises NmfpLoadError if the file or a required table is missing, or if the
    percentage scale cannot be determined.
    """
    path = Path(path)
    if not path.exists():
        raise NmfpLoadError(f"file not found: {path}")
    tables: dict[str, pd.DataFrame] = {}
    with zipfile.ZipFile(path) as zf:
        members = {_table_name(n): n for n in zf.namelist() if not n.endswith("/")}
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
    unparsed = _coerce(tables)
    scale = _percent_scale(tables["SCHPORTFOLIOSECURITIES"])
    _apply_percent_scale(tables, scale)
    tables["_UNPARSED"] = unparsed
    tables["_META"] = pd.DataFrame([{"source": path.name, "pct_multiplier": scale}])
    return tables


def read_table(path: str | Path, table: str, accessions: set[str] | None = None,
               chunksize: int = 200_000) -> pd.DataFrame:
    """Read one extra table (e.g. COLLATERALISSUERS, about 55MB raw) in chunks, keeping only
    rows for the given accessions. Values stay as text. Returns an empty frame if absent."""
    with zipfile.ZipFile(path) as zf:
        members = {_table_name(n): n for n in zf.namelist() if not n.endswith("/")}
        if table not in members:
            return pd.DataFrame()
        parts = []
        with zf.open(members[table]) as fh:
            for chunk in pd.read_csv(fh, sep="\t", dtype=str, keep_default_na=False, na_values=[""],
                                     encoding="utf-8", chunksize=chunksize):
                parts.append(chunk if accessions is None else chunk[chunk["ACCESSION_NUMBER"].isin(accessions)])
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


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
_PERCENT = {
    "SCHPORTFOLIOSECURITIES": ["PERCENTAGEOFMONEYMARKETFUNDNET"],
    "LIQUIDASSETSDETAILS": ["PCTDAILYLIQUIDASSETS", "PCTWEEKLYLIQUIDASSETS"],
}


def _to_date(raw: pd.Series) -> pd.Series:
    """SEC format first (30-JUN-2026), ISO 8601 as fallback (2026-06-30)."""
    out = pd.to_datetime(raw, format="%d-%b-%Y", errors="coerce")
    rest = raw.notna() & out.isna()
    if rest.any():
        out[rest] = pd.to_datetime(raw[rest], format="ISO8601", errors="coerce")
    return out


def _coerce(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    issues = []
    for spec, parse in ((_NUMERIC, lambda s: pd.to_numeric(s, errors="coerce")), (_DATES, _to_date)):
        for name, cols in spec.items():
            df = tables.get(name)
            if df is None or df.empty:
                continue
            for c in cols:
                if c not in df.columns:
                    continue
                raw = df[c]
                parsed = parse(raw)
                bad = raw.notna() & parsed.isna()
                if bad.any():
                    issues.append(pd.DataFrame({"ACCESSION_NUMBER": df.loc[bad, "ACCESSION_NUMBER"],
                                                "TABLE": name, "COLUMN": c, "VALUE": raw[bad]}))
                df[c] = parsed
    cols = ["ACCESSION_NUMBER", "TABLE", "COLUMN", "VALUE"]
    return pd.concat(issues, ignore_index=True) if issues else pd.DataFrame(columns=cols)


def _percent_scale(sec: pd.DataFrame) -> float:
    """Multiplier that puts percentage fields on a 0-100 scale, decided from the median
    holdings total per filing (about 1.0 when stored as fractions, about 100 when not)."""
    totals = sec.groupby("ACCESSION_NUMBER")["PERCENTAGEOFMONEYMARKETFUNDNET"].sum()
    median = totals.median()
    if 0.5 <= median <= 2.0:
        return 100.0
    if 50.0 <= median <= 200.0:
        return 1.0
    raise NmfpLoadError(f"cannot determine percentage scale: median holdings total per filing is {median}")


def _apply_percent_scale(tables: dict[str, pd.DataFrame], multiplier: float) -> None:
    if multiplier == 1.0:
        return
    for name, cols in _PERCENT.items():
        df = tables.get(name)
        if df is None or df.empty:
            continue
        for c in cols:
            if c in df.columns:
                # round off float noise from the multiplication (source precision is 0.01pp)
                df[c] = (df[c] * multiplier).round(6)


def latest_submissions(submission: pd.DataFrame) -> pd.DataFrame:
    """One row per (SERIESID, REPORTDATE): the most recently filed version.

    Amendments (N-MFP3/A etc.) supersede the original filing. 'NT' notices (inability
    to file on time) carry no data and are dropped.
    """
    df = submission.copy()
    df = df[~df["SUBMISSIONTYPE"].str.upper().str.startswith("NT")]
    df = df.sort_values(["SERIESID", "REPORTDATE", "FILING_DATE", "ACCESSION_NUMBER"])
    return df.groupby(["SERIESID", "REPORTDATE"], as_index=False).tail(1).reset_index(drop=True)
