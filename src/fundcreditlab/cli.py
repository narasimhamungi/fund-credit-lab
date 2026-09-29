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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fund-credit-lab")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="analyse a Form N-MFP data set ZIP")
    a.add_argument("--zip", required=True, help="path to the SEC N-MFP data set ZIP")
    a.add_argument("--report-date", help="YYYY-MM-DD (default: latest in the data set)")
    a.add_argument("--series", action="append", help="SERIESID to include (repeatable)")
    a.add_argument("--out", default="outputs", help="output directory")
    args = p.parse_args(argv)

    tables = load_nmfp_zip(args.zip)
    findings = validate(tables, latest_submissions(tables["SUBMISSION"]))
    results = series_metrics(tables, args.report_date, DEFAULT_LIMITS)
    if args.series:
        results = [m for m in results if m["series_id"] in set(args.series)]
    out = Path(args.out)
    (out / "memos").mkdir(parents=True, exist_ok=True)
    for m in results:
        (out / "memos" / f"{m['series_id']}_{m['report_date']:%Y-%m}.md").write_text(
            render_memo(m, findings), encoding="utf-8")
    with open(out / "summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["series_id", "name", "category", "report_date", "net_assets", "wam", "wal",
                    "dla_min_pct", "wla_min_pct", "top1_pct", "top5_pct", "flags"])
        for m in results:
            w.writerow([m["series_id"], m["name"], m["category"], f"{m['report_date']:%Y-%m-%d}",
                        m["net_assets"], m["wam"], m["wal"], m["dla_min_pct"], m["wla_min_pct"],
                        m["concentration"]["top1_pct"], m["concentration"]["top5_pct"],
                        "; ".join(m["flags"])])
    print(f"{len(results)} series analysed, {len(findings)} data-quality findings -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
