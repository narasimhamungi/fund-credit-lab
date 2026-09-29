"""Per-series credit-profile metrics from a loaded N-MFP data set."""
from __future__ import annotations

import pandas as pd

from .config import (DEFAULT_LIMITS, GOVERNMENT_CATEGORY_KEYWORDS,
                     LIQUIDITY_EXEMPT_CATEGORY_KEYWORD, Limits)
from .loader import latest_submissions
from .stress import daily_net_flows, stress_table, worst_outflow


def _liquidity_applies(category: str | None) -> bool:
    return not (category and LIQUIDITY_EXEMPT_CATEGORY_KEYWORD in category.lower())


def _is_government(category) -> bool:
    text = str(category).lower() if category is not None else ""
    return any(k in text for k in GOVERNMENT_CATEGORY_KEYWORDS)


def issuer_concentration(sec: pd.DataFrame) -> dict:
    """Non-government issuer exposure as % of net assets: largest issuer, top-5 share and
    Herfindahl index (0-1). US Treasury and agency securities are excluded (see config)."""
    empty = {"top1_issuer": None, "top1_pct": None, "top5_pct": None, "hhi": None}
    if sec.empty:
        return empty
    non_gov = sec[~sec["INVESTMENTCATEGORY"].map(_is_government)]
    if non_gov.empty:
        return empty
    by_issuer = (non_gov.groupby("NAMEOFISSUER")["PERCENTAGEOFMONEYMARKETFUNDNET"].sum()
                 .sort_values(ascending=False))
    shares = by_issuer / 100.0
    return {"top1_issuer": by_issuer.index[0], "top1_pct": float(by_issuer.iloc[0]),
            "top5_pct": float(by_issuer.head(5).sum()), "hhi": float((shares ** 2).sum())}


def category_mix(sec: pd.DataFrame) -> dict[str, float]:
    if sec.empty:
        return {}
    mix = sec.groupby(sec["INVESTMENTCATEGORY"].fillna("Unspecified"))[
        "PERCENTAGEOFMONEYMARKETFUNDNET"].sum().sort_values(ascending=False)
    return {k: float(v) for k, v in mix.items()}


def rating_coverage(sec: pd.DataFrame, nrsro: pd.DataFrame) -> dict:
    """Share of securities carrying at least one NRSRO rating on the security itself, and
    the share rated by each agency. Ratings are NOT mapped across agencies: scales differ."""
    n = len(sec)
    if n == 0 or nrsro.empty:
        return {"securities": n, "rated_share": None, "by_agency": {}}
    r = nrsro[nrsro["TYPE"].str.upper() == "SECURITY"]
    r = r.merge(sec[["ACCESSION_NUMBER", "SECURITY_ID"]], on=["ACCESSION_NUMBER", "SECURITY_ID"])
    rated = r.drop_duplicates(["ACCESSION_NUMBER", "SECURITY_ID"]).shape[0]
    by_agency = (r.drop_duplicates(["ACCESSION_NUMBER", "SECURITY_ID", "NAMEOFNRSRO"])
                 .groupby("NAMEOFNRSRO").size() / n)
    return {"securities": n, "rated_share": rated / n,
            "by_agency": {k: float(v) for k, v in by_agency.items()}}


def series_metrics(tables: dict[str, pd.DataFrame], report_date: str | None = None,
                   limits: Limits = DEFAULT_LIMITS) -> list[dict]:
    latest = latest_submissions(tables["SUBMISSION"])
    if report_date is not None:
        latest = latest[latest["REPORTDATE"] == pd.Timestamp(report_date)]
    else:
        latest = latest[latest["REPORTDATE"] == latest["REPORTDATE"].max()]
    sl = tables["SERIESLEVELINFO"].set_index("ACCESSION_NUMBER")
    la, flows, nrsro = tables["LIQUIDASSETSDETAILS"], tables["DLYSHAREHOLDERFLOWREPORT"], tables["NRSRO"]
    results: list[dict] = []
    for sub in latest.itertuples():
        a = sub.ACCESSION_NUMBER
        if a not in sl.index:
            continue
        row = sl.loc[a]
        cat = row.get("MONEYMARKETFUNDCATEGORY")
        name = getattr(sub, "NAMEOFSERIES", None)
        if not isinstance(name, str) or not name:
            name = getattr(sub, "SERIES_NAME", None)
        sec = tables["SCHPORTFOLIOSECURITIES"]
        sec = sec[sec["ACCESSION_NUMBER"] == a]
        net_assets = float(row["NETASSETOFSERIES"]) if pd.notna(row["NETASSETOFSERIES"]) else None
        wam, wal = row["AVERAGEPORTFOLIOMATURITY"], row["AVERAGELIFEMATURITY"]

        liq = la[la["ACCESSION_NUMBER"] == a].sort_values("TOTLIQUIDASSETSNEARPCTDATE") if not la.empty else la
        dla_min = float(liq["PCTDAILYLIQUIDASSETS"].min()) if not liq.empty else None
        wla_min = float(liq["PCTWEEKLYLIQUIDASSETS"].min()) if not liq.empty else None
        wla_val = float(liq["TOTVALUEWEEKLYLIQUIDASSETS"].iloc[-1]) if not liq.empty else None
        dla_val = float(liq["TOTVALUEDAILYLIQUIDASSETS"].iloc[-1]) if not liq.empty else None

        applies = _liquidity_applies(cat)
        headroom = {
            "wam_days": None if pd.isna(wam) else limits.wam_max_days - float(wam),
            "wal_days": None if pd.isna(wal) else limits.wal_max_days - float(wal),
            "dla_pp": (dla_min - limits.dla_min_pct) if (applies and dla_min is not None) else None,
            "wla_pp": (wla_min - limits.wla_min_pct) if (applies and wla_min is not None) else None,
        }
        conc = issuer_concentration(sec)
        net = daily_net_flows(flows, a)
        worst = worst_outflow(net, limits.stress_window_days) if not net.empty else None
        stress = stress_table(net_assets or 0.0, wla_val, dla_val, worst, limits)

        flags: list[str] = []
        for key, lim, thin in (("wam_days", "WAM above limit", limits.thin_wam_days),
                               ("wal_days", "WAL above limit", limits.thin_wal_days)):
            h = headroom[key]
            if h is not None and h < 0:
                flags.append(lim)
            elif h is not None and h < thin:
                flags.append(f"thin {key[:3].upper()} headroom ({h:.0f} days)")
        for key, name_, in (("dla_pp", "DLA"), ("wla_pp", "WLA")):
            h = headroom[key]
            if h is not None and h < 0:
                flags.append(f"{name_} below minimum")
            elif h is not None and h < limits.thin_liquidity_pp:
                flags.append(f"thin {name_} headroom ({h:.1f} pp)")
        if conc["top1_pct"] is not None and conc["top1_pct"] >= limits.concentration_flag_pct:
            flags.append(f"issuer concentration: {conc['top1_issuer']} {conc['top1_pct']:.1f}%")

        results.append({
            "accession": a, "series_id": sub.SERIESID, "name": name, "category": cat,
            "report_date": sub.REPORTDATE, "net_assets": net_assets,
            "wam": None if pd.isna(wam) else float(wam), "wal": None if pd.isna(wal) else float(wal),
            "dla_min_pct": dla_min, "wla_min_pct": wla_min, "liquidity_tested": applies,
            "headroom": headroom, "concentration": conc, "category_mix": category_mix(sec),
            "rating_coverage": rating_coverage(sec, nrsro[nrsro["ACCESSION_NUMBER"] == a] if not nrsro.empty else nrsro),
            "stress": stress, "flags": flags,
        })
    return results
