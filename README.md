# fund-credit-lab

![CI](https://github.com/narasimhamungi/fund-credit-lab/actions/workflows/ci.yml/badge.svg)

Credit-profile analytics for US money market funds, built from public SEC Form N-MFP data.
For each fund it computes maturity and liquidity headroom against Rule 2a-7 limits, credit concentration by
legal entity, repo counterparty exposure, rating coverage by agency and a liquidity stress, then writes a short
credit-profile memo.

> Independent illustration from public filings. **Not a credit rating** and not any agency's methodology.

## Status

- [x] Loader for the SEC N-MFP data set ZIP in its live layout (`NMFP_` member names, `DD-MON-YYYY` dates,
      percentages filed as fractions), with amendment handling
- [x] Data-quality validation, including unparsable values (findings carried into the memo, never silently fixed)
- [x] Metrics: WAM/WAL headroom, daily/weekly liquid assets against the Rule 2a-7 minimums and board-notification
      thresholds, credit concentration by legal entity, repo counterparties, category mix, rating coverage
- [x] Regulatory thresholds checked against the rule text (sources in `docs/limitations.md`)
- [x] Liquidity stress: rolling worst net outflow and instantaneous redemption shocks
- [x] Memo renderer and CLI
- [x] Unit tests on synthetic fixtures written in the live SEC layout
- [x] Run on the live SEC data set for 31 Aug 2026: 295 funds, outputs in `outputs/2026-08/`
- [x] Net assets, WAM, WAL and liquidity checked against sponsor disclosures for two funds (`docs/validation.md`)
- [ ] Concentration, repo and ratings reconciled to a published holdings file
- [x] `case` command: one fund's traceable extract (daily liquidity with peers, flows, top entities, repo
      counterparties and collateral, ratings by agency and scale, peer percentiles), unit-tested
- [x] Case study on JPMorgan Prime Money Market Fund: rationale and committee memo in
      [`docs/case-studies/jpmorgan-prime-2026-08/`](docs/case-studies/jpmorgan-prime-2026-08/)
- [x] Case-study deck: [`deck.pdf`](docs/case-studies/jpmorgan-prime-2026-08/deck.pdf)
- [x] Prospectus review with page references: [`prospectus-review.md`](docs/case-studies/jpmorgan-prime-2026-08/prospectus-review.md)

## Run

```bash
pip install -e ".[test]"
pytest -q
# download a Form N-MFP data set ZIP from https://www.sec.gov/dera/data/form-nmfp-data-sets
fund-credit-lab analyze --zip path/to/nmfp_data_set.zip --out outputs/2026-08
fund-credit-lab analyze --zip path/to/nmfp_data_set.zip --series S000000000 --report-date 2026-08-31
```

Case extract for one fund, with peers for the daily liquidity comparison:

```bash
fund-credit-lab case --zip path/to/nmfp_data_set.zip --series S000002969 --peer S000004283 --out outputs/2026-08
```

It writes `case_<SERIESID>/` with seven CSVs and `case_summary.md`; any figure a case-study document cites
comes from one of those files.

The latest report date in the ZIP is used unless `--report-date` is given. Feeder funds are left out unless
`--include-feeders` is passed.

Output: `summary.csv` (one row per series), `findings.csv` (data-quality findings) and
`memos/<SERIESID>_<YYYY-MM>.md`.

## Layout

| Path | Purpose |
|---|---|
| `src/fundcreditlab/loader.py` | Read the ZIP, parse types, detect the percentage scale, pick the latest filing per series and month |
| `src/fundcreditlab/validate.py` | Data-quality checks |
| `src/fundcreditlab/metrics.py` | Per-series profile metrics |
| `src/fundcreditlab/stress.py` | Liquidity stress |
| `src/fundcreditlab/report.py` | Memo rendering |
| `src/fundcreditlab/case.py` | One-fund case extract (reads `COLLATERALISSUERS` in chunks, filtered to the fund) |
| `docs/` | Data dictionary, engineering decisions, limitations, regulatory sources and live-data validation |

Read `docs/limitations.md` before using any output.
