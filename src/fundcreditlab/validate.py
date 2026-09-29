"""Data-quality checks on the loaded tables. Each check returns findings; nothing is
silently corrected. A finding never blocks analysis, but it is carried into the report."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# Percentages are filed to 0.01pp, so totals such as 100.01% are rounding, not errors.
PCT_TOLERANCE = 0.5


@dataclass(frozen=True)
class Finding:
    accession: str
    check: str
    detail: str


def validate(tables: dict[str, pd.DataFrame], latest: pd.DataFrame) -> list[Finding]:
    out: list[Finding] = []
    acc_latest = set(latest["ACCESSION_NUMBER"])

    unparsed = tables.get("_UNPARSED")
    if unparsed is not None and not unparsed.empty:
        for r in unparsed[unparsed["ACCESSION_NUMBER"].isin(acc_latest)].itertuples():
            out.append(Finding(r.ACCESSION_NUMBER, "unparsed_value",
                               f"{r.TABLE}.{r.COLUMN} = {r.VALUE!r} could not be parsed; treated as missing"))

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

    pct = "PERCENTAGEOFMONEYMARKETFUNDNET"
    sec = tables["SCHPORTFOLIOSECURITIES"]
    sec = sec[sec["ACCESSION_NUMBER"].isin(acc_latest)]
    if not sec.empty:
        totals = sec.groupby("ACCESSION_NUMBER")[pct].sum()
        for a, t in totals.items():
            if not 80.0 <= t <= 120.0:
                out.append(Finding(a, "holdings_total", f"holdings sum to {t:.1f}% of net assets"))
        bad = sec[(sec[pct] < 0) | (sec[pct] > 100 + PCT_TOLERANCE)]
        for r in bad.itertuples():
            out.append(Finding(r.ACCESSION_NUMBER, "pct_out_of_range", f"{r.NAMEOFISSUER}: {getattr(r, pct):g}%"))
        report = latest.set_index("ACCESSION_NUMBER")["REPORTDATE"]
        m = sec.assign(REP_DATE=sec["ACCESSION_NUMBER"].map(report))
        matured = m[m["INVESTMENTMATURITYDATEWAM"] < m["REP_DATE"]]
        for a, g in matured.groupby("ACCESSION_NUMBER"):
            r = g.iloc[0]
            example = (f"{r['NAMEOFISSUER']} matures {r['INVESTMENTMATURITYDATEWAM'].date()} "
                       f"before report date {r['REP_DATE'].date()}")
            detail = example if len(g) == 1 else f"{len(g)} holdings mature before the report date, e.g. {example}"
            out.append(Finding(a, "matured_holding", detail))

    la = tables["LIQUIDASSETSDETAILS"]
    if not la.empty:
        la = la[la["ACCESSION_NUMBER"].isin(acc_latest)]
        for col in ("PCTDAILYLIQUIDASSETS", "PCTWEEKLYLIQUIDASSETS"):
            bad = la[(la[col] < 0) | (la[col] > 100 + PCT_TOLERANCE)]
            for a, g in bad.groupby("ACCESSION_NUMBER"):
                out.append(Finding(a, "pct_out_of_range",
                                   f"{col} outside 0-100% on {len(g)} reported day(s), e.g. {g[col].iloc[0]:g}"))
        both = la.dropna(subset=["PCTDAILYLIQUIDASSETS", "PCTWEEKLYLIQUIDASSETS"])
        inverted = both[both["PCTWEEKLYLIQUIDASSETS"] < both["PCTDAILYLIQUIDASSETS"]]
        for a, g in inverted.groupby("ACCESSION_NUMBER"):
            out.append(Finding(a, "wla_lt_dla", f"weekly liquid % below daily liquid % on {len(g)} reported "
                                                "day(s) (weekly includes daily)"))
    return out
