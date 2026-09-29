# fund-credit-lab

![CI](https://github.com/narasimhamungi/fund-credit-lab/actions/workflows/ci.yml/badge.svg)

Credit-profile analytics for US money market funds, built from public SEC Form N-MFP data.
For each fund it computes maturity and liquidity headroom against Rule 2a-7 style limits, non-government issuer
concentration, rating coverage by agency and a liquidity stress, then writes a short credit-profile memo.

> Independent illustration from public filings. **Not a credit rating** and not any agency's methodology.

## Status

- [x] Loader for the SEC N-MFP data set ZIP, with amendment handling
- [x] Data-quality validation (findings carried into the memo, never silently fixed)
- [x] Metrics: WAM/WAL headroom, liquid assets, concentration, category mix, rating coverage
- [x] Liquidity stress: rolling worst net outflow and instantaneous redemption shocks
- [x] Memo renderer and CLI
- [x] Unit tests on synthetic fixtures built to the SEC table layout
- [ ] Run on a real SEC data set and commit dated outputs to `outputs/` (pending)

Until the last box is ticked, treat results as unvalidated on live data.

## Run

```bash
pip install -e ".[test]"
pytest -q
# download a Form N-MFP data set ZIP from https://www.sec.gov/dera/data/form-nmfp-data-sets
fund-credit-lab analyze --zip path/to/nmfp_data_set.zip --out outputs
fund-credit-lab analyze --zip path/to/nmfp_data_set.zip --series S000000000 --report-date 2026-06-30
```

Output: `outputs/summary.csv` (one row per series) and `outputs/memos/<SERIESID>_<YYYY-MM>.md`.

## Layout

| Path | Purpose |
|---|---|
| `src/fundcreditlab/loader.py` | Read the ZIP, coerce types, pick the latest filing per series and month |
| `src/fundcreditlab/validate.py` | Data-quality checks |
| `src/fundcreditlab/metrics.py` | Per-series profile metrics |
| `src/fundcreditlab/stress.py` | Liquidity stress |
| `src/fundcreditlab/report.py` | Memo rendering |
| `docs/` | Data dictionary, engineering decisions, limitations |

Read `docs/limitations.md` before using any output.
