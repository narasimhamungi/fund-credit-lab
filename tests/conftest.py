"""Synthetic Form N-MFP data set in the live SEC DERA layout (see docs/data_dictionary.md).

Nothing here is real fund data. Tables are written the way SEC publishes them: members
named NMFP_<TABLE>.tsv, dates as DD-MON-YYYY and percentages as fractions of 1.
write_zip(..., live=False) writes the older/hand-built layout (bare names, ISO dates,
0-100 percentages), which must load to the same numbers.

ALPHA   amended filing supersedes the original; ratings, flows, LEI grouping, non-government repo
GAMMA   government fund: thin headroom on every limit, one credit issuer, government repo
DELTA   Other Tax Exempt: daily minimum not tested, weekly minimum tested and missed
EPSILON bad data: WAL < WAM, holdings that do not sum, matured holding, unparsable value,
        weekly liquidity below the board-notification threshold
ZETA    Single State (tax-exempt): 3% daily liquidity must not be flagged
ETA     feeder fund holding its master fund
"""
import zipfile

import pandas as pd
import pytest

RD = "2026-01-31"
M = 1_000_000
LEI_BANK_X = "LEIBANKX000000000001"
TSY_REPO = "U.S. Treasury Repurchase Agreement, if collateralized only by U.S. Treasuries (including Strips) and cash"
AGY_REPO = ("U.S. Government Agency Repurchase Agreement, collateralized only by U.S. Government Agency "
            "securities, U.S. Treasuries, and cash")
OTHER_REPO = "Other Repurchase Agreement, if collateral falls outside Treasury, Government Agency and cash"

DATE_COLUMNS = {"FILING_DATE", "REPORTDATE", "INVESTMENTMATURITYDATEWAM", "TOTLIQUIDASSETSNEARPCTDATE",
                "DAILYSHAREHOLDERFLOWDATE"}
PCT_COLUMNS = {"PERCENTAGEOFMONEYMARKETFUNDNET", "PCTDAILYLIQUIDASSETS", "PCTWEEKLYLIQUIDASSETS"}


def _flows(acc, net_millions, start="2026-01-02"):
    dates = pd.bdate_range(start, periods=len(net_millions))
    rows = []
    for d, n in zip(dates, net_millions):
        rows.append({"ACCESSION_NUMBER": acc, "CLASSESID": "C000000001",
                     "DAILYGROSSSUBSCRIPTIONS": max(n, 0) * M,
                     "DAILYGROSSREDEMPTIONS": max(-n, 0) * M,
                     "DAILYSHAREHOLDERFLOWDATE": d.strftime("%Y-%m-%d")})
    return rows


def build_tables():
    def s(acc, filed, typ, sid, name):
        return dict(ACCESSION_NUMBER=acc, FILING_DATE=filed, SUBMISSIONTYPE=typ, REPORTDATE=RD,
                    SERIESID=sid, NAMEOFSERIES=name, SERIES_NAME=name.split()[0].upper())

    sub = [
        s("0001-26-000001", "2026-02-05", "N-MFP3", "S000000001", "Alpha Prime Fund"),
        s("0001-26-000002", "2026-02-10", "N-MFP3/A", "S000000001", "Alpha Prime Fund"),
        s("0002-26-000001", "2026-02-05", "N-MFP3", "S000000002", "Gamma Government Fund"),
        s("0003-26-000001", "2026-02-05", "N-MFP3", "S000000003", "Delta Tax Exempt Fund"),
        s("0004-26-000001", "2026-02-05", "N-MFP3", "S000000004", "Epsilon Bad Data Fund"),
        s("0005-26-000001", "2026-02-07", "NT N-MFP3", "S000000001", "Alpha Prime Fund"),
        s("0006-26-000001", "2026-02-05", "N-MFP3", "S000000005", "Zeta Single State Fund"),
        s("0007-26-000001", "2026-02-05", "N-MFP3", "S000000006", "Eta Feeder Fund"),
    ]

    def sl(acc, cat, wam, wal, na, feeder="N"):
        return dict(ACCESSION_NUMBER=acc, MONEYMARKETFUNDCATEGORY=cat, FEEDERFUNDFLAG=feeder,
                    AVERAGEPORTFOLIOMATURITY=wam, AVERAGELIFEMATURITY=wal, NETASSETOFSERIES=na * M)

    sls = [
        sl("0001-26-000001", "Prime", 45, 90, 1000),
        sl("0001-26-000002", "Prime", 30, 70, 1000),
        sl("0002-26-000001", "Government", 58, 118, 500),
        sl("0003-26-000001", "Other Tax Exempt", 20, 40, 200),
        sl("0004-26-000001", "Prime", 40, 30, 100),
        sl("0006-26-000001", "Single State", 25, 50, 150),
        sl("0007-26-000001", "Prime", 30, 60, 300, feeder="Y"),
    ]

    def sec(acc, sid, issuer, cat, pct, mat="2026-03-15", lei=None):
        return dict(ACCESSION_NUMBER=acc, SECURITY_ID=sid, NAMEOFISSUER=issuer, LEI=lei, INVESTMENTCATEGORY=cat,
                    PERCENTAGEOFMONEYMARKETFUNDNET=pct, INVESTMENTMATURITYDATEWAM=mat)

    a = "0001-26-000002"
    secs = [
        sec(a, 1, "BANK X", "Financial Company Commercial Paper", 5, lei=LEI_BANK_X),
        sec(a, 2, "BANK Y", "Certificate of Deposit", 6),
        sec(a, 3, "US TREASURY", "U.S. Treasury Debt", 81),
        sec(a, 4, "Bank X Inc.", "Certificate of Deposit", 3, lei=LEI_BANK_X),   # same legal entity as BANK X
        sec(a, 5, "DEALER C", OTHER_REPO, 5, mat="2026-02-02"),
        sec("0002-26-000001", 1, "FINCO Z", "Financial Company Commercial Paper", 12),
        sec("0002-26-000001", 2, "US TREASURY", "U.S. Treasury Debt", 48),
        sec("0002-26-000001", 3, "DEALER A", TSY_REPO, 30, mat="2026-02-02"),
        sec("0002-26-000001", 4, "DEALER B", AGY_REPO, 10, mat="2026-02-02"),
        sec("0003-26-000001", 1, "STATE MUNI", "Other Municipal Security", 60),
        sec("0003-26-000001", 2, "CITY MUNI", "Other Municipal Security", 40),
        sec("0004-26-000001", 1, "ODD CORP", "Financial Company Commercial Paper", 30),
        sec("0004-26-000001", 2, "OLD PAPER", "Certificate of Deposit", 20, mat="2026-01-15"),
        sec("0006-26-000001", 1, "STATE A HFA", "Variable Rate Demand Note", 55),
        sec("0006-26-000001", 2, "STATE A GO", "Other Municipal Security", 45),
        sec("0007-26-000001", 1, "MASTER PRIME PORTFOLIO", "Investment Company", 100),
    ]
    nr = [   # agency names as they appear in live filings; one agency can be named several ways
        dict(ACCESSION_NUMBER=a, SECURITY_ID=1, IDENTITY=None, TYPE="SECURITY",
             NAMEOFNRSRO="Standard and Poor's Ratings Services", RATING="A-1+"),
        dict(ACCESSION_NUMBER=a, SECURITY_ID=1, IDENTITY=None, TYPE="SECURITY", NAMEOFNRSRO="Fitch Short Rating", RATING="F1+"),
        dict(ACCESSION_NUMBER=a, SECURITY_ID=1, IDENTITY=None, TYPE="SECURITY", NAMEOFNRSRO="Fitch Long Rating", RATING="AA"),
        dict(ACCESSION_NUMBER=a, SECURITY_ID=2, IDENTITY=None, TYPE="SECURITY",
             NAMEOFNRSRO="Moody's Investors Service, Inc.", RATING="P-1"),
        dict(ACCESSION_NUMBER=a, SECURITY_ID=4, IDENTITY=None, TYPE="SECURITY", NAMEOFNRSRO=None, RATING="A-1"),
        dict(ACCESSION_NUMBER=a, SECURITY_ID=3, IDENTITY="GUARANTOR CO", TYPE="GUARANTOR",
             NAMEOFNRSRO="Fitch", RATING="AAA"),
        dict(ACCESSION_NUMBER=a, SECURITY_ID=5, IDENTITY=None, TYPE="SECURITY", NAMEOFNRSRO="N/A", RATING="N/A"),
        # ETA files placeholder entries only, as one large live filer does
        dict(ACCESSION_NUMBER="0007-26-000001", SECURITY_ID=1, IDENTITY=None, TYPE="SECURITY",
             NAMEOFNRSRO="N/A", RATING="N/A"),
    ]

    def liq(acc, date, dv, wv, dp, wp):
        return dict(ACCESSION_NUMBER=acc, TOTVALUEDAILYLIQUIDASSETS=dv, TOTVALUEWEEKLYLIQUIDASSETS=wv,
                    PCTDAILYLIQUIDASSETS=dp, PCTWEEKLYLIQUIDASSETS=wp, TOTLIQUIDASSETSNEARPCTDATE=date)

    la = [
        liq(a, "2026-01-02", 400 * M, 650 * M, 40, 65),
        liq(a, "2026-01-09", 380 * M, 600 * M, 38, 60),
        liq("0002-26-000001", "2026-01-30", 130 * M, 255 * M, 26, 51),
        liq("0003-26-000001", "2026-01-30", 10 * M, 60 * M, 5, 30),
        liq("0004-26-000001", "2026-01-29", 31 * M, 21 * M, "n/a", 21),   # unparsable value
        liq("0004-26-000001", "2026-01-30", 30 * M, 20 * M, 30, 20),
        liq("0006-26-000001", "2026-01-30", 4.5 * M, 90 * M, 3, 60),
        liq("0007-26-000001", "2026-01-30", 180 * M, 240 * M, 60, 80),
    ]
    fl = _flows(a, [10, -20, -30, -10, 5, -15])
    return {"SUBMISSION": sub, "SERIESLEVELINFO": sls, "SCHPORTFOLIOSECURITIES": secs,
            "NRSRO": nr, "LIQUIDASSETSDETAILS": la, "DLYSHAREHOLDERFLOWREPORT": fl}


def _live_value(column, value):
    """Convert a readable fixture value to the live SEC representation."""
    if value is None:
        return value
    if column in DATE_COLUMNS:
        return pd.Timestamp(value).strftime("%d-%b-%Y").upper()
    if column in PCT_COLUMNS:
        try:
            return round(float(value) / 100.0, 6)
        except (TypeError, ValueError):
            return value
    return value


def write_zip(path, tables=None, extension=".tsv", drop=(), live=True):
    tables = tables or build_tables()
    with zipfile.ZipFile(path, "w") as zf:
        for name, rows in tables.items():
            if name in drop:
                continue
            if live:
                rows = [{k: _live_value(k, v) for k, v in r.items()} for r in rows]
            member = ("NMFP_" + name if live else name) + extension
            zf.writestr(member, pd.DataFrame(rows).to_csv(sep="\t", index=False))
    return path


@pytest.fixture
def nmfp_zip(tmp_path):
    return write_zip(tmp_path / "nmfp.zip")


@pytest.fixture
def legacy_zip(tmp_path):
    return write_zip(tmp_path / "legacy.zip", live=False)
