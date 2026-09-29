"""One-fund case extract: the traceable numbers behind a written case study.

`fund-credit-lab case --zip DATA.zip --series S000002969 --peer S000004283` writes CSVs and a
summary to <out>/case_<SERIESID>/. Every figure a case-study document cites should come from
one of these files. Nothing here is a rating; see docs/limitations.md.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import DEFAULT_LIMITS, Limits
from .loader import read_table
from .metrics import PCT, _annotate, _grouped_exposure, _is_placeholder, agency, series_metrics
from .stress import daily_net_flows

_SHORT_TERM = re.compile(r"^(A-1\+?|A-2|A-3|P-1|P-2|P-3|F1\+?|F2|F3|K1\+?|K2|K3|R-1.*|R-2.*|SP-1\+?|SP-2|"
                         r"V?MIG ?\d)$", re.IGNORECASE)


def rating_scale(code) -> str:
    """'short-term' when the code matches a known short-term symbol, else 'long-term/other'.
    Pattern-based: a label, not a mapping between agencies."""
    return "short-term" if isinstance(code, str) and _SHORT_TERM.match(code.strip()) else "long-term/other"


def _percentile(values: pd.Series, x: float | None) -> float | None:
    v = values.dropna()
    if x is None or pd.isna(x) or v.empty:
        return None
    return float((v <= x).mean() * 100.0)


def liquidity_daily(tables: dict, accessions: dict[str, str]) -> pd.DataFrame:
    la = tables["LIQUIDASSETSDETAILS"]
    cols = ["series_id", "date", "dla_pct", "wla_pct", "dla_usd", "wla_usd"]
    if la.empty:
        return pd.DataFrame(columns=cols)
    rows = la[la["ACCESSION_NUMBER"].isin(accessions)].copy()
    out = pd.DataFrame({"series_id": rows["ACCESSION_NUMBER"].map(accessions),
                        "date": rows["TOTLIQUIDASSETSNEARPCTDATE"].dt.strftime("%Y-%m-%d"),
                        "dla_pct": rows["PCTDAILYLIQUIDASSETS"], "wla_pct": rows["PCTWEEKLYLIQUIDASSETS"],
                        "dla_usd": rows["TOTVALUEDAILYLIQUIDASSETS"], "wla_usd": rows["TOTVALUEWEEKLYLIQUIDASSETS"]})
    return out.sort_values(["series_id", "date"]).reset_index(drop=True)


def flows_daily(tables: dict, accession: str, window: int) -> pd.DataFrame:
    net = daily_net_flows(tables["DLYSHAREHOLDERFLOWREPORT"], accession)
    if net.empty:
        return pd.DataFrame(columns=["date", "net_flow_usd", f"rolling_{window}d_net_usd"])
    return pd.DataFrame({"date": net.index.strftime("%Y-%m-%d"), "net_flow_usd": net.values,
                         f"rolling_{window}d_net_usd": net.rolling(window, min_periods=window).sum().values})


def top_entities(sec: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    pool = sec[sec["_BUCKET"].isin(["credit", "other_repo"])]
    rows = [{"rank": i + 1, "entity": name, "pct_of_net_assets": round(pct, 4)}
            for i, (name, pct) in enumerate(_grouped_exposure(pool)[:n])]
    return pd.DataFrame(rows, columns=["rank", "entity", "pct_of_net_assets"])


def repo_counterparties(sec: pd.DataFrame, collateral: pd.DataFrame) -> pd.DataFrame:
    """Per counterparty (legal entity): repo % of net assets split by collateral type, and
    collateral value / position value where both are filed."""
    cols = ["counterparty", "pct_of_net_assets", "gov_collateral_pct", "other_collateral_pct", "positions",
            "position_usd", "collateral_usd", "collateral_to_position"]
    repo = sec[sec["_BUCKET"].isin(["government_repo", "other_repo"])]
    if repo.empty:
        return pd.DataFrame(columns=cols)
    coll = pd.Series(dtype=float)
    if not collateral.empty:
        cv = pd.to_numeric(collateral["VALUEOFCOLLATERALTOTHENEARESTC"], errors="coerce")
        coll = cv.groupby(collateral["SECURITY_ID"]).sum()
    out = []
    for _, g in repo.groupby("_KEY", sort=False):
        label = g.sort_values(PCT, ascending=False)["NAMEOFISSUER"].iloc[0]
        pos_usd = None
        if "INCLUDINGVALUEOFANYSPONSORSUPP" in g.columns and g["INCLUDINGVALUEOFANYSPONSORSUPP"].notna().any():
            pos_usd = float(pd.to_numeric(g["INCLUDINGVALUEOFANYSPONSORSUPP"], errors="coerce").sum())
        c_usd = float(coll.reindex(g["SECURITY_ID"]).sum()) if not coll.empty else 0.0
        c_usd = c_usd or None
        out.append({"counterparty": label, "pct_of_net_assets": float(g[PCT].sum()),
                    "gov_collateral_pct": float(g.loc[g["_BUCKET"] == "government_repo", PCT].sum()),
                    "other_collateral_pct": float(g.loc[g["_BUCKET"] == "other_repo", PCT].sum()),
                    "positions": len(g), "position_usd": pos_usd, "collateral_usd": c_usd,
                    "collateral_to_position": (c_usd / pos_usd) if (c_usd and pos_usd) else None})
    df = pd.DataFrame(out, columns=cols).sort_values("pct_of_net_assets", ascending=False)
    return df.reset_index(drop=True)


def repo_collateral(sec: pd.DataFrame, collateral: pd.DataFrame) -> pd.DataFrame:
    """Collateral behind the fund's repo, by collateral category and repo type."""
    cols = ["repo_type", "collateral_category", "collateral_usd", "share_of_repo_type_pct"]
    if collateral.empty:
        return pd.DataFrame(columns=cols)
    bucket = sec.set_index("SECURITY_ID")["_BUCKET"]
    c = collateral.assign(repo_type=collateral["SECURITY_ID"].map(bucket),
                          value=pd.to_numeric(collateral["VALUEOFCOLLATERALTOTHENEARESTC"], errors="coerce"),
                          category=collateral["CTGRYINVESTMENTSRPRSNTSCOLLATE"].fillna("Not stated"))
    c = c[c["repo_type"].isin(["government_repo", "other_repo"])]
    if c.empty:
        return pd.DataFrame(columns=cols)
    g = c.groupby(["repo_type", "category"])["value"].sum().reset_index()
    g["share_of_repo_type_pct"] = g["value"] / g.groupby("repo_type")["value"].transform("sum") * 100.0
    g = g.rename(columns={"category": "collateral_category", "value": "collateral_usd"})
    return g.sort_values(["repo_type", "collateral_usd"], ascending=[True, False]).reset_index(drop=True)[cols]


def ratings_by_agency(sec: pd.DataFrame, nrsro: pd.DataFrame) -> pd.DataFrame:
    """Security-level ratings as filed, per agency and rating code, as % of net assets.
    Placeholders ('N/A') are excluded. A security can carry a short- and a long-term rating
    from the same agency, so shares are shown per scale, never summed across scales."""
    cols = ["agency", "scale", "rating", "pct_of_net_assets", "securities"]
    if nrsro.empty:
        return pd.DataFrame(columns=cols)
    r = nrsro[nrsro["TYPE"].astype(str).str.upper() == "SECURITY"]
    r = r[r["RATING"].notna() & ~r["RATING"].map(_is_placeholder) & ~r["NAMEOFNRSRO"].map(_is_placeholder)]
    if r.empty:
        return pd.DataFrame(columns=cols)
    r = r.assign(agency=r["NAMEOFNRSRO"].map(agency), rating=r["RATING"].str.strip(),
                 scale=r["RATING"].map(rating_scale))
    r = r.drop_duplicates(["SECURITY_ID", "agency", "rating"])
    pct = sec.set_index("SECURITY_ID")[PCT]
    r = r.assign(pct=r["SECURITY_ID"].map(pct))
    g = (r.groupby(["agency", "scale", "rating"]).agg(pct_of_net_assets=("pct", "sum"), securities=("SECURITY_ID", "nunique"))
         .reset_index().sort_values(["agency", "scale", "pct_of_net_assets"], ascending=[True, False, False]))
    return g.reset_index(drop=True)[cols]


def peer_stats(all_metrics: list[dict], case: dict) -> pd.DataFrame:
    """Where the fund sits among non-feeder funds of the same category at the same report date."""
    peers = [m for m in all_metrics if m["category"] == case["category"] and not m["feeder"]]
    getters = {
        "wla_min_pct": lambda m: m["wla_min_pct"],
        "dla_min_pct": lambda m: m["dla_min_pct"] if m["dla_tested"] else None,
        "wam_days": lambda m: m["wam"],
        "wal_days": lambda m: m["wal"],
        "top1_entity_pct": lambda m: m["concentration"]["top1_pct"],
        "top5_entities_pct": lambda m: m["concentration"]["top5_pct"],
        "repo_pct": lambda m: m["repo"]["repo_pct"],
        "other_collateral_repo_pct": lambda m: m["repo"]["other_collateral_pct"],
        "rated_pct_of_assets": lambda m: m["rating_coverage"]["rated_pct_of_assets"],
    }
    rows = []
    for metric, get in getters.items():
        vals = pd.Series([get(m) for m in peers], dtype=float)
        x = get(case)
        v = vals.dropna()
        rows.append({"metric": metric, "fund": x, "peers": int(v.size),
                     "p25": float(v.quantile(0.25)) if v.size else None,
                     "median": float(v.median()) if v.size else None,
                     "p75": float(v.quantile(0.75)) if v.size else None,
                     "fund_percentile": _percentile(vals, x)})
    return pd.DataFrame(rows)


def _fmt(v, spec="{:.1f}"):
    return "n/a" if v is None or (isinstance(v, float) and pd.isna(v)) else spec.format(v)


def build_case(zip_path: str | Path, tables: dict, series_id: str, peers: list[str] | None = None,
               report_date: str | None = None, limits: Limits = DEFAULT_LIMITS) -> dict:
    """Compute every case table for one series. Raises ValueError if the series is not filed."""
    results = series_metrics(tables, report_date, limits)
    by_id = {m["series_id"]: m for m in results}
    if series_id not in by_id:
        raise ValueError(f"{series_id} has no filing for the report date")
    case = by_id[series_id]
    acc = case["accession"]
    sec = _annotate(tables["SCHPORTFOLIOSECURITIES"])
    sec = sec[sec["ACCESSION_NUMBER"] == acc]
    nrsro = tables["NRSRO"]
    nrsro = nrsro[nrsro["ACCESSION_NUMBER"] == acc] if not nrsro.empty else nrsro
    collateral = read_table(zip_path, "COLLATERALISSUERS", {acc})
    peer_acc = {by_id[p]["accession"]: p for p in (peers or []) if p in by_id}
    missing_peers = [p for p in (peers or []) if p not in by_id]
    liq = liquidity_daily(tables, {acc: series_id, **peer_acc})
    return {
        "case": case, "missing_peers": missing_peers,
        "liquidity_daily": liq,
        "flows_daily": flows_daily(tables, acc, limits.stress_window_days),
        "top_entities": top_entities(sec),
        "repo_counterparties": repo_counterparties(sec, collateral),
        "repo_collateral": repo_collateral(sec, collateral),
        "ratings_by_agency": ratings_by_agency(sec, nrsro),
        "peer_stats": peer_stats(results, case),
        "collateral_rows": len(collateral),
    }


def render_summary(c: dict, source: str, limits: Limits = DEFAULT_LIMITS) -> str:
    m = c["case"]
    sid = m["series_id"]
    L = [f"# Case extract: {m['name']} ({sid})",
         f"Report date {m['report_date']:%Y-%m-%d} · Category {m['category']} · Source `{source}`", "",
         "*Independent illustration from public SEC Form N-MFP data. Not a credit rating, and not the methodology "
         "of any rating agency. Every figure below is in a CSV in this folder.*", "",
         "## Headline (memo and summary.csv)",
         f"- Net assets ${_fmt(m['net_assets'], '{:,.0f}')}; WAM {_fmt(m['wam'], '{:.0f}')} days; WAL {_fmt(m['wal'], '{:.0f}')} days",
         f"- Lowest DLA {_fmt(m['dla_min_pct'], '{:.2f}')}% on {m.get('dla_min_date') or 'n/a'}; lowest WLA "
         f"{_fmt(m['wla_min_pct'], '{:.2f}')}% on {m.get('wla_min_date') or 'n/a'}"]
    liq = c["liquidity_daily"]
    own = liq[liq["series_id"] == sid]
    if not own.empty:
        last = own.iloc[-1]
        below_w = int((own["wla_pct"] < limits.wla_min_pct).sum())
        below_d = int((own["dla_pct"] < limits.dla_min_pct).sum()) if m["dla_tested"] else None
        L.append(f"- Month-end ({last['date']}): DLA {_fmt(last['dla_pct'], '{:.2f}')}%, WLA {_fmt(last['wla_pct'], '{:.2f}')}%; "
                 f"reported days {len(own)}; days below {limits.wla_min_pct:g}% WLA: {below_w}; days below "
                 f"{limits.dla_min_pct:g}% DLA: {_fmt(below_d, '{:d}')}  (`liquidity_daily.csv`)")
    fl = c["flows_daily"]
    if not fl.empty:
        col = fl.columns[-1]
        worst = fl[col].min()
        when = fl.loc[fl[col].idxmin(), "date"] if pd.notna(worst) else None
        L.append(f"- Worst rolling {limits.stress_window_days}-day net flow ${_fmt(worst, '{:,.0f}')} ending {when or 'n/a'}; "
                 f"net flow over the month ${_fmt(fl['net_flow_usd'].sum(), '{:,.0f}')}  (`flows_daily.csv`)")
    L += ["", "## Peer position (`peer_stats.csv`)",
          f"Peers: non-feeder {m['category']} funds at the same report date. Percentile = share of peers at or below the fund.", "",
          "| Metric | Fund | Peers | P25 | Median | P75 | Fund percentile |", "|---|---|---|---|---|---|---|"]
    for r in c["peer_stats"].itertuples():
        L.append(f"| {r.metric} | {_fmt(r.fund, '{:.2f}')} | {r.peers} | {_fmt(r.p25, '{:.2f}')} | {_fmt(r.median, '{:.2f}')} | "
                 f"{_fmt(r.p75, '{:.2f}')} | {_fmt(r.fund_percentile, '{:.0f}')} |")
    L += ["", "## Largest credit entities (`top_entities.csv`)"]
    for r in c["top_entities"].itertuples():
        L.append(f"{r.rank}. {r.entity}: {r.pct_of_net_assets:.2f}%")
    L += ["", "## Repo (`repo_counterparties.csv`, `repo_collateral.csv`)"]
    rp = c["repo_counterparties"]
    if rp.empty:
        L.append("- No repo positions.")
    else:
        L.append(f"- {len(rp)} counterparties; top five:")
        for r in rp.head(5).itertuples():
            L.append(f"  - {r.counterparty}: {r.pct_of_net_assets:.2f}% (other collateral {r.other_collateral_pct:.2f}%); "
                     f"collateral/position {_fmt(r.collateral_to_position, '{:.3f}')}")
        rc = c["repo_collateral"]
        if rc.empty:
            L.append(f"- Collateral detail: none found ({c['collateral_rows']} collateral rows for this filing).")
        else:
            for t in ("other_repo", "government_repo"):
                sub = rc[rc["repo_type"] == t]
                if not sub.empty:
                    mix = "; ".join(f"{x.collateral_category} {x.share_of_repo_type_pct:.1f}%" for x in sub.head(6).itertuples())
                    L.append(f"- Collateral behind {t.replace('_', ' ')}: {mix}")
    L += ["", "## Ratings as filed (`ratings_by_agency.csv`)"]
    ra = c["ratings_by_agency"]
    if ra.empty:
        L.append("- No security-level ratings reported (placeholders excluded).")
    else:
        for (ag, sc), g in ra.groupby(["agency", "scale"], sort=True):
            top = "; ".join(f"{x.rating} {x.pct_of_net_assets:.1f}%" for x in g.head(4).itertuples())
            L.append(f"- {ag}, {sc}: {top}")
    if c["missing_peers"]:
        L += ["", f"Peers not found for this report date: {', '.join(c['missing_peers'])}"]
    return "\n".join(L) + "\n"


def write_case(c: dict, out_dir: Path, source: str) -> Path:
    d = Path(out_dir) / f"case_{c['case']['series_id']}"
    d.mkdir(parents=True, exist_ok=True)
    for name in ("liquidity_daily", "flows_daily", "top_entities", "repo_counterparties", "repo_collateral",
                 "ratings_by_agency", "peer_stats"):
        c[name].to_csv(d / f"{name}.csv", index=False, float_format="%.6g")
    (d / "case_summary.md").write_text(render_summary(c, source), encoding="utf-8")
    return d
