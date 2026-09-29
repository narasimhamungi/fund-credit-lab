"""Render a credit-profile memo in markdown from computed metrics.

This is an independent analytical illustration built from public filings. It is not
a credit rating, not a Fitch product, and does not apply any agency's methodology.
"""
from __future__ import annotations

from .config import DEFAULT_LIMITS, Limits
from .validate import Finding

DISCLAIMER = ("*Independent illustration from public SEC Form N-MFP data. Not a credit rating, "
              "and not the methodology of any rating agency.*")
FEEDER_NOTE = ("*Feeder fund: its portfolio is shares of a master fund, so concentration and rating "
               "coverage describe that holding, not the underlying issuers.*")


def _f(v, fmt="{:.1f}", na="n/a"):
    return na if v is None else fmt.format(v)


def render_memo(m: dict, findings: list[Finding] | None = None, limits: Limits = DEFAULT_LIMITS) -> str:
    lim = limits
    h, c, s, rp = m["headroom"], m["concentration"], m["stress"], m["repo"]
    L: list[str] = []
    L.append(f"# {m['name'] or m['series_id']} ({m['series_id']})")
    L.append(f"Report date: {m['report_date']:%Y-%m-%d}  |  Category: {m['category']}  |  "
             f"Net assets: ${_f(m['net_assets'], '{:,.0f}')}")
    L.append("")
    L.append(DISCLAIMER)
    if m.get("feeder"):
        L.append("")
        L.append(FEEDER_NOTE)
    L.append("")
    L.append("## Key profile drivers")
    L.append(f"- **Maturity:** WAM {_f(m['wam'])} days (limit {lim.wam_max_days:g}), WAL {_f(m['wal'])} days (limit {lim.wal_max_days:g}).")
    if m["dla_tested"]:
        L.append(f"- **Liquidity:** lowest daily liquid assets {_f(m['dla_min_pct'])}% (minimum {lim.dla_min_pct:g}%) and lowest "
                 f"weekly liquid assets {_f(m['wla_min_pct'])}% (minimum {lim.wla_min_pct:g}%) of total assets in the month.")
    else:
        L.append(f"- **Liquidity:** lowest weekly liquid assets {_f(m['wla_min_pct'])}% (minimum {lim.wla_min_pct:g}%). The daily "
                 f"minimum does not apply to tax-exempt funds; lowest daily liquid assets {_f(m['dla_min_pct'])}% "
                 "shown for information.")
    if c["top1_issuer"] is None:
        L.append("- **Credit concentration:** none; holdings are US government securities and "
                 "government-collateralised repo only.")
    else:
        L.append(f"- **Credit concentration (legal entity):** largest {c['top1_issuer']} at {_f(c['top1_pct'])}% of "
                 f"net assets; top five {_f(c['top5_pct'])}%; Herfindahl {_f(c['hhi'], '{:.3f}')}.")
    if rp["repo_pct"]:
        L.append(f"- **Repo:** {rp['repo_pct']:.1f}% of net assets across {rp['counterparties']} counterparties "
                 f"(government collateral {rp['gov_collateral_pct']:.1f}%, other collateral "
                 f"{rp['other_collateral_pct']:.1f}%); largest counterparty {rp['top_counterparty']} at "
                 f"{rp['top_counterparty_pct']:.1f}%, gross of collateral.")
    rc = m["rating_coverage"]
    if rc["reported"]:
        agencies = ", ".join(f"{k} {v:.0%}" for k, v in sorted(rc["by_agency"].items())) or "none"
        L.append(f"- **Rating coverage (as filed):** {rc['rated_share']:.0%} of {rc['securities']} securities, "
                 f"{rc['rated_pct_of_assets']:.1f}% of net assets, carry a security-level NRSRO rating "
                 f"({agencies}). Ratings are shown per agency, not mapped across scales.")
    else:
        L.append("- **Rating coverage:** no NRSRO ratings reported in this filing. Absence in the data does not "
                 "mean the holdings are unrated.")
    L.append("")
    L.append("## Portfolio mix (% of net assets)")
    for k, v in list(m["category_mix"].items())[:8]:
        L.append(f"- {k}: {v:.1f}%")
    L.append("")
    L.append("## Headroom to limits")
    L.append("| Measure | Headroom |")
    L.append("|---|---|")
    L.append(f"| WAM vs {lim.wam_max_days:g}-day limit | {_f(h['wam_days'])} days |")
    L.append(f"| WAL vs {lim.wal_max_days:g}-day limit | {_f(h['wal_days'])} days |")
    dla = _f(h["dla_pp"]) + " pp" if m["dla_tested"] else "not applicable (tax-exempt)"
    L.append(f"| Daily liquid assets vs {lim.dla_min_pct:g}% minimum | {dla} |")
    L.append(f"| Weekly liquid assets vs {lim.wla_min_pct:g}% minimum | {_f(h['wla_pp'])} pp |")
    L.append("")
    L.append("## Liquidity stress")
    if s["worst_outflow"] is not None:
        L.append(f"- Worst cumulative net outflow over the stress window: ${s['worst_outflow']:,.0f} "
                 f"({_f(s['worst_outflow_pct_of_assets'], '{:.2f}')}% of net assets); weekly liquid assets "
                 f"cover it {_f(s['weekly_coverage_of_worst_outflow'], '{:.1f}')}x.")
    else:
        L.append("- No daily shareholder-flow data in this filing, so historical-flow stress is not run.")
    L.append("")
    L.append("| Instant redemption | Amount | Covered by daily liquid | Covered by weekly liquid |")
    L.append("|---|---|---|---|")
    for x in s["shocks"]:
        cd = "n/a" if x["covered_by_daily"] is None else ("yes" if x["covered_by_daily"] else "no")
        cw = "n/a" if x["covered_by_weekly"] is None else ("yes" if x["covered_by_weekly"] else "no")
        L.append(f"| {x['shock_pct']:.0f}% | ${x['amount']:,.0f} | {cd} | {cw} |")
    L.append("")
    L.append("## What would weaken the profile")
    if m["flags"]:
        for fl in m["flags"]:
            L.append(f"- {fl}")
    else:
        L.append("- No screening flags. Sensitivities: lengthening WAM or WAL toward the limits, a fall in weekly "
                 "liquid assets toward the minimum, or growth in single-issuer exposure.")
    if findings:
        mine = [f for f in findings if f.accession == m["accession"]]
        if mine:
            L.append("")
            L.append("## Data-quality findings")
            for f in mine:
                L.append(f"- `{f.check}`: {f.detail}")
    return "\n".join(L) + "\n"
