"""Per-series credit-profile metrics from a loaded N-MFP data set."""
from __future__ import annotations

import pandas as pd

from .config import DEFAULT_LIMITS, TAX_EXEMPT_CATEGORIES, Limits
from .loader import latest_submissions
from .stress import daily_net_flows, stress_table, worst_outflow

PCT = "PERCENTAGEOFMONEYMARKETFUNDNET"


def is_tax_exempt(category) -> bool:
    return isinstance(category, str) and category.strip().lower() in TAX_EXEMPT_CATEGORIES


def holding_bucket(category) -> str:
    """Classify an INVESTMENTCATEGORY string (exact SEC wording, see docs/data_dictionary.md).

    government       US Treasury and agency debt
    government_repo  repo collateralised only by Treasury/agency securities and cash
    other_repo       repo with any other collateral (credit exposure to the counterparty)
    credit           everything else, including unknown or missing categories
    """
    text = category.strip().lower() if isinstance(category, str) else ""
    if "repurchase agreement" in text:
        return "other_repo" if text.startswith("other") else "government_repo"
    if text.startswith(("u.s. treasury debt", "u.s. government agency debt")):
        return "government"
    return "credit"


def issuer_keys(df: pd.DataFrame) -> pd.Series:
    """Legal-entity key per holding: the LEI where a 20-character LEI is filed, else the
    upper-cased issuer name."""
    key = "NAME:" + df["NAMEOFISSUER"].fillna("Unknown").astype(str).str.upper().str.strip()
    if "LEI" in df.columns:
        lei = df["LEI"].astype("string").str.strip()
        key = key.where(~(lei.str.len() == 20).fillna(False), "LEI:" + lei)
    return key


def _annotate(sec: pd.DataFrame) -> pd.DataFrame:
    """Add the bucket and legal-entity key once, so per-fund work stays cheap."""
    if "_BUCKET" in sec.columns or sec.empty:
        return sec
    return sec.assign(_BUCKET=sec["INVESTMENTCATEGORY"].map(holding_bucket), _KEY=issuer_keys(sec))


def _grouped_exposure(df: pd.DataFrame) -> list[tuple[str, float]]:
    """[(label, % of net assets)] per legal entity, largest first. Label = issuer name on
    the entity's largest position."""
    totals: dict[str, float] = {}
    label: dict[str, tuple[float, str]] = {}
    names = df["NAMEOFISSUER"].fillna("Unknown").astype(str)
    for key, name, pct in zip(df["_KEY"], names, df[PCT]):
        if pd.isna(pct):
            continue
        totals[key] = totals.get(key, 0.0) + float(pct)
        if key not in label or pct > label[key][0]:
            label[key] = (float(pct), name)
    return sorted(((label[k][1], v) for k, v in totals.items()), key=lambda x: -x[1])


def issuer_concentration(sec: pd.DataFrame) -> dict:
    """Credit exposure by legal entity as % of net assets: largest, top five and Herfindahl
    (0-1). Excludes Treasury/agency debt and government-collateralised repo; includes
    repo with other collateral."""
    empty = {"top1_issuer": None, "top1_pct": None, "top5_pct": None, "hhi": None}
    if sec.empty:
        return empty
    sec = _annotate(sec)
    g = _grouped_exposure(sec[sec["_BUCKET"].isin(["credit", "other_repo"])])
    if not g:
        return empty
    return {"top1_issuer": g[0][0], "top1_pct": g[0][1], "top5_pct": sum(v for _, v in g[:5]),
            "hhi": sum((v / 100.0) ** 2 for _, v in g)}


def repo_exposure(sec: pd.DataFrame) -> dict:
    """Repo as % of net assets, split by collateral type, and the largest counterparty
    (gross of collateral)."""
    out = {"repo_pct": 0.0, "gov_collateral_pct": 0.0, "other_collateral_pct": 0.0,
           "top_counterparty": None, "top_counterparty_pct": None, "counterparties": 0}
    if sec.empty:
        return out
    sec = _annotate(sec)
    repo = sec[sec["_BUCKET"].isin(["government_repo", "other_repo"])]
    g = _grouped_exposure(repo)
    if not g:
        return out
    out.update(repo_pct=float(repo[PCT].sum()),
               gov_collateral_pct=float(repo.loc[repo["_BUCKET"] == "government_repo", PCT].sum()),
               other_collateral_pct=float(repo.loc[repo["_BUCKET"] == "other_repo", PCT].sum()),
               top_counterparty=g[0][0], top_counterparty_pct=g[0][1], counterparties=len(g))
    return out


def category_mix(sec: pd.DataFrame) -> dict[str, float]:
    if sec.empty:
        return {}
    mix = sec.groupby(sec["INVESTMENTCATEGORY"].fillna("Unspecified"))[PCT].sum().sort_values(ascending=False)
    return {k: float(v) for k, v in mix.items()}


_AGENCIES = (("fitch", "Fitch"), ("moody", "Moody's"), ("standard", "S&P"), ("s&p", "S&P"),
             ("dbrs", "DBRS Morningstar"), ("morningstar", "DBRS Morningstar"), ("kroll", "KBRA"),
             ("kbra", "KBRA"))
UNNAMED_AGENCY = "agency not named"


def agency(name) -> str:
    """Normalise NAMEOFNRSRO: live filings name one agency several ways ('Fitch Long Rating',
    'Fitch Short Rating', 'Standard and Poor's Ratings Services', 'Standard & Poor's Long Rating')."""
    if not isinstance(name, str) or not name.strip():
        return UNNAMED_AGENCY
    low = name.lower()
    for key, label in _AGENCIES:
        if key in low:
            return label
    return name.strip()


def rating_coverage(sec: pd.DataFrame, nrsro: pd.DataFrame) -> dict:
    """Security-level NRSRO ratings as filed: share of securities with at least one rating,
    the same share weighted by % of net assets, and the share rated by each agency.
    Ratings are NOT mapped across agencies: scales differ. reported=False means the filing
    carries no rating rows at all."""
    n = len(sec)
    out = {"securities": n, "reported": False, "rated_share": None, "rated_pct_of_assets": None,
           "by_agency": {}}
    if n == 0 or nrsro.empty:
        return out
    r = nrsro[nrsro["TYPE"].astype(str).str.upper() == "SECURITY"]
    r = r[r["RATING"].notna()] if "RATING" in r.columns else r
    r = r.assign(AGENCY=r["NAMEOFNRSRO"].map(agency))
    r = r.merge(sec[["ACCESSION_NUMBER", "SECURITY_ID"]], on=["ACCESSION_NUMBER", "SECURITY_ID"])
    rated_ids = set(r["SECURITY_ID"])
    by_agency = r.drop_duplicates(["SECURITY_ID", "AGENCY"]).groupby("AGENCY").size() / n
    out.update(reported=True, rated_share=len(rated_ids) / n,
               rated_pct_of_assets=float(sec.loc[sec["SECURITY_ID"].isin(rated_ids), PCT].sum()),
               by_agency={k: float(v) for k, v in by_agency.items()})
    return out


def _low_point(liq: pd.DataFrame, col: str) -> tuple[float | None, str | None]:
    """Lowest reported value in the month and the date it was reported."""
    if liq.empty or liq[col].isna().all():
        return None, None
    i = liq[col].idxmin()
    d = liq.loc[i, "TOTLIQUIDASSETSNEARPCTDATE"]
    return float(liq.loc[i, col]), (None if pd.isna(d) else f"{d:%Y-%m-%d}")


def _liquidity_flag(label: str, low: float | None, when: str | None, minimum: float, notify: float,
                    thin: float) -> str | None:
    if low is None or pd.isna(low):
        return None
    on = f" on {when}" if when else ""
    if low < notify:
        return f"{label} fell to {low:.1f}%{on}, below the {notify:g}% board-notification threshold"
    if low < minimum:
        return (f"{label} fell to {low:.1f}%{on}, below the {minimum:g}% acquisition minimum "
                f"(not a breach; restricts new purchases)")
    if low - minimum < thin:
        return f"thin {label} headroom ({low - minimum:.1f} pp)"
    return None


def _by_accession(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if df.empty or "ACCESSION_NUMBER" not in df.columns:
        return {}
    return {k: g for k, g in df.groupby("ACCESSION_NUMBER", sort=False)}


def series_metrics(tables: dict[str, pd.DataFrame], report_date: str | None = None,
                   limits: Limits = DEFAULT_LIMITS) -> list[dict]:
    """Metrics for every series filed for the report date (default: latest in the data).
    Feeder funds are included and marked; the CLI leaves them out unless asked."""
    latest = latest_submissions(tables["SUBMISSION"])
    if report_date is not None:
        latest = latest[latest["REPORTDATE"] == pd.Timestamp(report_date)]
    else:
        latest = latest[latest["REPORTDATE"] == latest["REPORTDATE"].max()]
    sl = tables["SERIESLEVELINFO"].set_index("ACCESSION_NUMBER")
    sec_all = _annotate(tables["SCHPORTFOLIOSECURITIES"])
    sec_by = _by_accession(sec_all)
    la_by = _by_accession(tables["LIQUIDASSETSDETAILS"])
    nr_by = _by_accession(tables["NRSRO"])
    fl_by = _by_accession(tables["DLYSHAREHOLDERFLOWREPORT"])
    empty = pd.DataFrame()
    results: list[dict] = []
    for sub in latest.itertuples():
        a = sub.ACCESSION_NUMBER
        if a not in sl.index:
            continue
        row = sl.loc[a]
        cat = row.get("MONEYMARKETFUNDCATEGORY")
        feeder = str(row.get("FEEDERFUNDFLAG", "")).strip().upper() == "Y"
        name = getattr(sub, "NAMEOFSERIES", None)
        if not isinstance(name, str) or not name:
            name = getattr(sub, "SERIES_NAME", None)
        sec = sec_by.get(a, sec_all.iloc[0:0])
        net_assets = float(row["NETASSETOFSERIES"]) if pd.notna(row["NETASSETOFSERIES"]) else None
        wam, wal = row["AVERAGEPORTFOLIOMATURITY"], row["AVERAGELIFEMATURITY"]

        liq = la_by.get(a, empty)
        if not liq.empty:
            liq = liq.sort_values("TOTLIQUIDASSETSNEARPCTDATE")
        dla_min, dla_min_date = _low_point(liq, "PCTDAILYLIQUIDASSETS")
        wla_min, wla_min_date = _low_point(liq, "PCTWEEKLYLIQUIDASSETS")
        wla_val = float(liq["TOTVALUEWEEKLYLIQUIDASSETS"].iloc[-1]) if not liq.empty else None
        dla_val = float(liq["TOTVALUEDAILYLIQUIDASSETS"].iloc[-1]) if not liq.empty else None

        dla_tested = not is_tax_exempt(cat)
        headroom = {
            "wam_days": None if pd.isna(wam) else limits.wam_max_days - float(wam),
            "wal_days": None if pd.isna(wal) else limits.wal_max_days - float(wal),
            "dla_pp": (dla_min - limits.dla_min_pct) if (dla_tested and dla_min is not None) else None,
            "wla_pp": (wla_min - limits.wla_min_pct) if wla_min is not None else None,
        }
        conc = issuer_concentration(sec)
        repo = repo_exposure(sec)
        net = daily_net_flows(fl_by.get(a, empty), a)
        worst = worst_outflow(net, limits.stress_window_days) if not net.empty else None
        stress = stress_table(net_assets or 0.0, wla_val, dla_val, worst, limits)

        flags: list[str] = []
        if feeder:
            flags.append("feeder fund: portfolio is shares of its master fund; analyse the master series")
        for key, lim, thin in (("wam_days", "WAM above limit", limits.thin_wam_days),
                               ("wal_days", "WAL above limit", limits.thin_wal_days)):
            h = headroom[key]
            if h is not None and h < 0:
                flags.append(lim)
            elif h is not None and h < thin:
                flags.append(f"thin {key[:3].upper()} headroom ({h:.0f} days)")
        if dla_tested:
            f = _liquidity_flag("DLA", dla_min, dla_min_date, limits.dla_min_pct, limits.dla_notify_pct,
                                limits.thin_liquidity_pp)
            if f:
                flags.append(f)
        f = _liquidity_flag("WLA", wla_min, wla_min_date, limits.wla_min_pct, limits.wla_notify_pct,
                            limits.thin_liquidity_pp)
        if f:
            flags.append(f)
        if not feeder and conc["top1_pct"] is not None and conc["top1_pct"] >= limits.concentration_flag_pct:
            flags.append(f"issuer concentration: {conc['top1_issuer']} {conc['top1_pct']:.1f}%")

        results.append({
            "accession": a, "series_id": sub.SERIESID, "name": name, "category": cat,
            "report_date": sub.REPORTDATE, "net_assets": net_assets, "feeder": feeder,
            "wam": None if pd.isna(wam) else float(wam), "wal": None if pd.isna(wal) else float(wal),
            "dla_min_pct": dla_min, "wla_min_pct": wla_min, "dla_min_date": dla_min_date,
            "wla_min_date": wla_min_date, "dla_tested": dla_tested,
            "headroom": headroom, "concentration": conc, "repo": repo, "category_mix": category_mix(sec),
            "rating_coverage": rating_coverage(sec, nr_by.get(a, empty)),
            "stress": stress, "flags": flags,
        })
    return results
