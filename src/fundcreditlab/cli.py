"""Command line entry point: fund-credit-lab analyze --zip DATA.zip [--report-date YYYY-MM-DD]."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .config import DEFAULT_LIMITS
from .loader import latest_submissions, load_nmfp_zip
from .metrics import series_metrics
from .report import render_memo
from .validate import validate

SUMMARY_COLUMNS = ["series_id", "name", "category", "report_date", "net_assets", "wam", "wal",
                   "dla_min_pct", "wla_min_pct", "dla_tested", "top1_issuer", "top1_pct", "top5_pct",
                   "repo_pct", "top_repo_counterparty", "top_repo_counterparty_pct", "rated_pct_of_assets", "flags"]


def _r(v, digits=2):
    return None if v is None else round(v, digits)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fund-credit-lab")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="analyse a Form N-MFP data set ZIP")
    a.add_argument("--zip", required=True, help="path to the SEC N-MFP data set ZIP")
    a.add_argument("--report-date", help="YYYY-MM-DD (default: latest in the data set)")
    a.add_argument("--series", action="append", help="SERIESID to include (repeatable)")
    a.add_argument("--include-feeders", action="store_true",
                   help="also write memos for feeder funds (their portfolio is the master fund)")
    a.add_argument("--out", default="outputs", help="output directory")
    c = sub.add_parser("case", help="write the traceable extract for one fund's case study")
    c.add_argument("--zip", required=True, help="path to the SEC N-MFP data set ZIP")
    c.add_argument("--series", required=True, help="SERIESID of the fund")
    c.add_argument("--peer", action="append", help="SERIESID to include in the daily liquidity file (repeatable)")
    c.add_argument("--report-date", help="YYYY-MM-DD (default: latest in the data set)")
    c.add_argument("--out", default="outputs", help="output directory; files go to <out>/case_<SERIESID>/")
    args = p.parse_args(argv)

    tables = load_nmfp_zip(args.zip)
    if args.cmd == "case":
        return _case(args, tables)
    results = series_metrics(tables, args.report_date, DEFAULT_LIMITS)
    feeders = [m for m in results if m["feeder"]]
    if not args.include_feeders:
        results = [m for m in results if not m["feeder"]]
    if args.series:
        results = [m for m in results if m["series_id"] in set(args.series)]
    latest = latest_submissions(tables["SUBMISSION"])
    findings = validate(tables, latest[latest["ACCESSION_NUMBER"].isin({m["accession"] for m in results})])

    out = Path(args.out)
    (out / "memos").mkdir(parents=True, exist_ok=True)
    for m in results:
        (out / "memos" / f"{m['series_id']}_{m['report_date']:%Y-%m}.md").write_text(
            render_memo(m, findings, DEFAULT_LIMITS), encoding="utf-8")
    with open(out / "summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(SUMMARY_COLUMNS)
        for m in results:
            c, r = m["concentration"], m["repo"]
            w.writerow([m["series_id"], m["name"], m["category"], f"{m['report_date']:%Y-%m-%d}",
                        m["net_assets"], m["wam"], m["wal"], _r(m["dla_min_pct"]), _r(m["wla_min_pct"]),
                        m["dla_tested"], c["top1_issuer"], _r(c["top1_pct"]), _r(c["top5_pct"]),
                        _r(r["repo_pct"]), r["top_counterparty"], _r(r["top_counterparty_pct"]),
                        _r(m["rating_coverage"]["rated_pct_of_assets"]),
                        "; ".join(m["flags"])])
    series_of = {m["accession"]: m["series_id"] for m in results}
    with open(out / "findings.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["series_id", "accession", "check", "detail"])
        for f in findings:
            w.writerow([series_of.get(f.accession), f.accession, f.check, f.detail])

    multiplier = float(tables["_META"]["pct_multiplier"].iloc[0])
    scale = "fractions, converted to %" if multiplier != 1.0 else "already in %"
    skipped = "" if args.include_feeders else f"; {len(feeders)} feeder funds left out (--include-feeders to add)"
    print(f"{len(results)} series analysed{skipped}; {len(findings)} data-quality findings; "
          f"percentages filed as {scale} -> {out}/")
    return 0


def _case(args, tables) -> int:
    from .case import build_case, write_case
    try:
        c = build_case(args.zip, tables, args.series, args.peer, args.report_date, DEFAULT_LIMITS)
    except ValueError as e:
        print(f"error: {e}")
        return 2
    d = write_case(c, Path(args.out), Path(args.zip).name)
    note = f"; peers not found: {', '.join(c['missing_peers'])}" if c["missing_peers"] else ""
    print(f"case extract for {args.series} -> {d}/ ({c['collateral_rows']} collateral rows{note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
