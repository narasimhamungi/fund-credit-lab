"""Render a credit-profile memo in markdown from computed metrics.

This is an independent analytical illustration built from public filings. It is not
a credit rating, not a Fitch product, and does not apply any agency's methodology.
"""
from __future__ import annotations

from .validate import Finding

DISCLAIMER = ("*Independent illustration from public SEC Form N-MFP data. Not a credit rating, "
              "and not the methodology of any rating agency.*")


def _f(v, fmt="{:.1f}", na="n/a"):
    return na if v is None else fmt.format(v)


def render_memo(m: dict, findings: list[Finding] | None = None) -> str:
    h, c, s = m["headroom"], m["concentration"], m["stress"]
    L: list[str] = []
    L.append(f"# {m['name'] or m['series_id']} ({m['series_id']})")
    L.append(f"Report date: {m['report_date']:%Y-%m-%d}  |  Category: {m['category']}  |  "
             f"Net assets: ${_f(m['net_assets'], '{:,.0f}')}")
    L.append("")
    L.append(DISCLAIMER)
    L.append("")
    L.append("## Key profile drivers")
    L.append(f"- **Maturity:** WAM {_f(m['wam'])} days, WAL {_f(m['wal'])} days.")
    if m["liquidity_tested"]:
        L.append(f"- **Liquidity:** lowest daily liquid assets {_f(m['dla_min_pct'])}% and lowest weekly "
                 f"liquid assets {_f(m['wla_min_pct'])}% of total assets in the reporting month.")
    else:
        L.append("- **Liquidity:** category is not tested against the daily/weekly minimums here "
                 f"(observed lowest DLA {_f(m['dla_min_pct'])}%, WLA {_f(m['wla_min_pct'])}%).")
    if c["top1_issuer"] is None:
        L.append("- **Concentration (non-government issuers):** none; the portfolio holds only US government securities.")
    else:
        L.append(f"- **Concentration (non-government issuers):** largest issuer {c['top1_issuer']} at "
                 f"{_f(c['top1_pct'])}% of net assets; top five {_f(c['top5_pct'])}%; "
                 f"Herfindahl {_f(c['hhi'], '{:.3f}')}.")
    rc = m["rating_coverage"]
    if rc["rated_share"] is not None:
        agencies = ", ".join(f"{k} {v:.0%}" for k, v in sorted(rc["by_agency"].items())) or "none"
        L.append(f"- **Rating coverage:** {rc['rated_share']:.0%} of {rc['securities']} securities carry an "
                 f"NRSRO rating ({agencies}). Ratings are shown per agency, not mapped across scales.")
    L.append("")
    L.append("## Portfolio mix (% of net assets)")
    for k, v in list(m["category_mix"].items())[:8]:
        L.append(f"- {k}: {v:.1f}%")
    L.append("")
    L.append("## Headroom to limits")
    L.append("| Measure | Headroom |")
    L.append("|---|---|")
    L.append(f"| WAM vs limit | {_f(h['wam_days'])} days |")
    L.append(f"| WAL vs limit | {_f(h['wal_days'])} days |")
    L.append(f"| Daily liquid assets vs minimum | {_f(h['dla_pp'])} pp |")
    L.append(f"| Weekly liquid assets vs minimum | {_f(h['wla_pp'])} pp |")
    L.append("")
    L.append("## Liquidity stress")
    if s["worst_outflow"] is not None:
        L.append(f"- Worst cumulative net outflow over the stress window: ${s['worst_outflow']:,.0f} "
                 f"({_f(s['worst_outflow_pct_of_assets'], '{:.2f}')}% of net assets); weekly liquid assets "
                 f"cover it {_f(s['weekly_coverage_of_worst_outflow'], '{:.1f}')}x.")
    else:
        L.append("- No daily shareholder-flow data in this filing (legacy form), so historical-flow stress is not run.")
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
