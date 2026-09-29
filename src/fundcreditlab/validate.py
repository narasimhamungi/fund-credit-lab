"""Data-quality checks on the loaded tables. Each check returns findings; nothing is
silently corrected. A finding never blocks analysis, but it is carried into the report."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Finding:
    accession: str
    check: str
    detail: str


def validate(tables: dict[str, pd.DataFrame], latest: pd.DataFrame) -> list[Finding]:
    out: list[Finding] = []
    acc_latest = set(latest["ACCESSION_NUMBER"])
    sl = tables["SERIESLEVELINFO"]
    sl = sl[sl["ACCESSION_NUMBER"].isin(acc_latest)]
    for r in sl.itertuples():
        a = r.ACCESSION_NUMBER
        wam, wal = r.AVERAGEPORTFOLIOMATURITY, r.AVERAGELIFEMATURITY
        for label, v in (("WAM", wam), ("WAL", wal), ("net assets", r.NETASSETOFSERIES)):
            if pd.isna(v):
                out.append(Finding(a, "missing_value", f"{label} is missing"))
        if pd.notna(wam) and pd.notna(wal) and wal < wam:
            out.append(Finding(a, "wal_lt_wam", f"WAL {wal:g} is below WAM {wam:g}"))
        if pd.notna(wam) and wam < 0:
            out.append(Finding(a, "negative_wam", f"WAM {wam:g}"))

    sec = tables["SCHPORTFOLIOSECURITIES"]
    sec = sec[sec["ACCESSION_NUMBER"].isin(acc_latest)]
    if not sec.empty:
        totals = sec.groupby("ACCESSION_NUMBER")["PERCENTAGEOFMONEYMARKETFUNDNET"].sum()
        for a, t in totals.items():
            if not 80.0 <= t <= 120.0:
                out.append(Finding(a, "holdings_total", f"holdings sum to {t:.1f}% of net assets"))
        bad = sec[(sec["PERCENTAGEOFMONEYMARKETFUNDNET"] < 0) |
                  (sec["PERCENTAGEOFMONEYMARKETFUNDNET"] > 100)]
        for r in bad.itertuples():
            out.append(Finding(r.ACCESSION_NUMBER, "pct_out_of_range",
                               f"{r.NAMEOFISSUER}: {r.PERCENTAGEOFMONEYMARKETFUNDNET:g}%"))
        report = latest.set_index("ACCESSION_NUMBER")["REPORTDATE"]
        for r in sec.itertuples():
            mat = r.INVESTMENTMATURITYDATEWAM
            rep = report.get(r.ACCESSION_NUMBER)
            if pd.notna(mat) and pd.notna(rep) and mat < rep:
                out.append(Finding(r.ACCESSION_NUMBER, "matured_holding",
                                   f"{r.NAMEOFISSUER} matures {mat.date()} before report date {rep.date()}"))

    la = tables["LIQUIDASSETSDETAILS"]
    if not la.empty:
        la = la[la["ACCESSION_NUMBER"].isin(acc_latest)]
        for col in ("PCTDAILYLIQUIDASSETS", "PCTWEEKLYLIQUIDASSETS"):
            bad = la[(la[col] < 0) | (la[col] > 100)]
            for r in bad.itertuples():
                out.append(Finding(r.ACCESSION_NUMBER, "pct_out_of_range", f"{col}={getattr(r, col):g}"))
        both = la.dropna(subset=["PCTDAILYLIQUIDASSETS", "PCTWEEKLYLIQUIDASSETS"])
        for r in both[both["PCTWEEKLYLIQUIDASSETS"] < both["PCTDAILYLIQUIDASSETS"]].itertuples():
            out.append(Finding(r.ACCESSION_NUMBER, "wla_lt_dla",
                               "weekly liquid % below daily liquid % (weekly includes daily)"))
    return out
