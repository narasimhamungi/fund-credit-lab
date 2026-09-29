"""Synthetic Form N-MFP data set, built to the SEC DERA table layout (see docs/data_dictionary.md).

Nothing here is real fund data. Each series is designed to exercise one behaviour:
ALPHA   amended filing supersedes the original; ratings, liquidity and flow stress
GAMMA   thin headroom on every limit plus single-issuer concentration
DELTA   tax-exempt category: liquid-asset minimums are not tested
EPSILON deliberately bad data: WAL < WAM, holdings that do not sum, a matured holding
"""
import zipfile

import pandas as pd
import pytest

RD = "2026-01-31"
M = 1_000_000


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
    sub = [
        dict(ACCESSION_NUMBER="0001-26-000001", FILING_DATE="2026-02-05", SUBMISSIONTYPE="N-MFP3",
             REPORTDATE=RD, SERIESID="S000000001", NAMEOFSERIES="Alpha Prime Fund", SERIES_NAME="ALPHA"),
        dict(ACCESSION_NUMBER="0001-26-000002", FILING_DATE="2026-02-10", SUBMISSIONTYPE="N-MFP3/A",
             REPORTDATE=RD, SERIESID="S000000001", NAMEOFSERIES="Alpha Prime Fund", SERIES_NAME="ALPHA"),
        dict(ACCESSION_NUMBER="0002-26-000001", FILING_DATE="2026-02-05", SUBMISSIONTYPE="N-MFP3",
             REPORTDATE=RD, SERIESID="S000000002", NAMEOFSERIES="Gamma Government Fund", SERIES_NAME="GAMMA"),
        dict(ACCESSION_NUMBER="0003-26-000001", FILING_DATE="2026-02-05", SUBMISSIONTYPE="N-MFP3",
             REPORTDATE=RD, SERIESID="S000000003", NAMEOFSERIES="Delta Tax Exempt Fund", SERIES_NAME="DELTA"),
        dict(ACCESSION_NUMBER="0004-26-000001", FILING_DATE="2026-02-05", SUBMISSIONTYPE="N-MFP3",
             REPORTDATE=RD, SERIESID="S000000004", NAMEOFSERIES="Epsilon Bad Data Fund", SERIES_NAME="EPSILON"),
        dict(ACCESSION_NUMBER="0005-26-000001", FILING_DATE="2026-02-07", SUBMISSIONTYPE="NT N-MFP3",
             REPORTDATE=RD, SERIESID="S000000001", NAMEOFSERIES="Alpha Prime Fund", SERIES_NAME="ALPHA"),
    ]
    sl = [
        dict(ACCESSION_NUMBER="0001-26-000001", MONEYMARKETFUNDCATEGORY="Prime",
             AVERAGEPORTFOLIOMATURITY=45, AVERAGELIFEMATURITY=90, NETASSETOFSERIES=1000 * M),
        dict(ACCESSION_NUMBER="0001-26-000002", MONEYMARKETFUNDCATEGORY="Prime",
             AVERAGEPORTFOLIOMATURITY=30, AVERAGELIFEMATURITY=70, NETASSETOFSERIES=1000 * M),
        dict(ACCESSION_NUMBER="0002-26-000001", MONEYMARKETFUNDCATEGORY="Government",
             AVERAGEPORTFOLIOMATURITY=58, AVERAGELIFEMATURITY=118, NETASSETOFSERIES=500 * M),
        dict(ACCESSION_NUMBER="0003-26-000001", MONEYMARKETFUNDCATEGORY="Other Tax Exempt",
             AVERAGEPORTFOLIOMATURITY=20, AVERAGELIFEMATURITY=40, NETASSETOFSERIES=200 * M),
        dict(ACCESSION_NUMBER="0004-26-000001", MONEYMARKETFUNDCATEGORY="Prime",
             AVERAGEPORTFOLIOMATURITY=40, AVERAGELIFEMATURITY=30, NETASSETOFSERIES=100 * M),
    ]

    def sec(acc, sid, issuer, cat, pct, mat="2026-03-15"):
        return dict(ACCESSION_NUMBER=acc, SECURITY_ID=sid, NAMEOFISSUER=issuer, INVESTMENTCATEGORY=cat,
                    PERCENTAGEOFMONEYMARKETFUNDNET=pct, INVESTMENTMATURITYDATEWAM=mat)

    a = "0001-26-000002"
    secs = [
        sec(a, 1, "BANK X", "Financial Company Commercial Paper", 8),
        sec(a, 2, "BANK Y", "Certificate of Deposit", 6),
        sec(a, 3, "US TREASURY", "U.S. Treasury Debt", 86),
        sec("0002-26-000001", 1, "FINCO Z", "Financial Company Commercial Paper", 12),
        sec("0002-26-000001", 2, "US TREASURY", "U.S. Treasury Debt", 88),
        sec("0003-26-000001", 1, "STATE MUNI", "Other Municipal Security", 60),
        sec("0003-26-000001", 2, "CITY MUNI", "Other Municipal Security", 40),
        sec("0004-26-000001", 1, "ODD CORP", "Financial Company Commercial Paper", 30),
        sec("0004-26-000001", 2, "OLD PAPER", "Certificate of Deposit", 20, mat="2026-01-15"),
    ]
    nr = [
        dict(ACCESSION_NUMBER=a, SECURITY_ID=1, IDENTITY=None, TYPE="SECURITY", NAMEOFNRSRO="S&P", RATING="A-1+"),
        dict(ACCESSION_NUMBER=a, SECURITY_ID=1, IDENTITY=None, TYPE="SECURITY", NAMEOFNRSRO="Fitch", RATING="F1+"),
        dict(ACCESSION_NUMBER=a, SECURITY_ID=2, IDENTITY=None, TYPE="SECURITY", NAMEOFNRSRO="Moody's", RATING="P-1"),
        dict(ACCESSION_NUMBER=a, SECURITY_ID=3, IDENTITY="GUARANTOR CO", TYPE="GUARANTOR",
             NAMEOFNRSRO="Fitch", RATING="AAA"),
    ]

    def liq(acc, date, dv, wv, dp, wp):
        return dict(ACCESSION_NUMBER=acc, TOTVALUEDAILYLIQUIDASSETS=dv, TOTVALUEWEEKLYLIQUIDASSETS=wv,
                    PCTDAILYLIQUIDASSETS=dp, PCTWEEKLYLIQUIDASSETS=wp, TOTLIQUIDASSETSNEARPCTDATE=date)

    la = [
        liq(a, "2026-01-02", 400 * M, 650 * M, 40, 65),
        liq(a, "2026-01-09", 380 * M, 600 * M, 38, 60),
        liq("0002-26-000001", "2026-01-30", 130 * M, 255 * M, 26, 51),
        liq("0003-26-000001", "2026-01-30", 10 * M, 60 * M, 5, 30),
        liq("0004-26-000001", "2026-01-30", 30 * M, 20 * M, 30, 20),
    ]
    fl = _flows(a, [10, -20, -30, -10, 5, -15])
    return {"SUBMISSION": sub, "SERIESLEVELINFO": sl, "SCHPORTFOLIOSECURITIES": secs,
            "NRSRO": nr, "LIQUIDASSETSDETAILS": la, "DLYSHAREHOLDERFLOWREPORT": fl}


def write_zip(path, tables=None, extension=".tsv", drop=()):
    tables = tables or build_tables()
    with zipfile.ZipFile(path, "w") as zf:
        for name, rows in tables.items():
            if name in drop:
                continue
            zf.writestr(name + extension, pd.DataFrame(rows).to_csv(sep="\t", index=False))
    return path


@pytest.fixture
def nmfp_zip(tmp_path):
    return write_zip(tmp_path / "nmfp.zip")
