# Engineering decisions

1. **Local ZIP as input.** The tool reads a data set ZIP you download from SEC. It does not
   fetch it, because I could not verify a stable download URL pattern and a wrong guess would fail silently.
2. **Amendments supersede originals.** For each (`SERIESID`, `REPORTDATE`) only the most
   recently filed submission is analysed. `NT` notices carry no data and are dropped.
3. **Nothing is silently fixed.** `validate.py` returns findings (missing values, unparsable values, WAL below
   WAM, holdings that do not sum to roughly 100%, matured holdings, liquid-asset percentages out of range). They are
   printed in the memo and written to `findings.csv`; they never alter a number.
4. **No cross-agency rating mapping.** Rating scales differ and the short-term scales do
   not line up one-to-one, so ratings are reported as coverage per agency and never converted to a single score.
5. **Credit concentration is measured on credit exposure only.** Treasury and agency debt and repo collateralised
   only by government securities are excluded; repo with other collateral is included, because the fund's exposure
   is to the counterparty. Positions are grouped by legal entity (LEI where filed, else issuer name). The 10% flag is
   an analyst screening threshold, not a rule.
6. **Repo is reported separately.** Total repo, the split by collateral type, and the largest counterparty (gross of
   collateral). Most funds in the data set are government funds, whose main non-government exposure is repo
   counterparties; without this view their memos would say almost nothing about counterparty risk.
7. **Limits are configuration.** WAM, WAL, liquid-asset minimums and board-notification thresholds live in
   `config.py`; sources are in `limitations.md`.
8. **Two liquidity tiers.** Below 25% daily / 50% weekly the fund may only buy liquid assets (an acquisition test,
   not a breach); below 12.5% / 25% the board must be notified. Flags say which tier was hit.
9. **Tax-exempt funds skip the daily test only.** `Single State` and `Other Tax Exempt` funds are tax-exempt funds;
   the daily minimum does not apply to them, the weekly minimum does.
10. **Feeder funds are left out by default.** A feeder's portfolio is shares of its master fund, so its concentration
    and ratings describe that single holding. `--include-feeders` adds them, with a note in the memo.
11. **Percentage scale is detected, not assumed.** Live files store fractions; older or hand-built files may use
    0-100. The loader decides from the median holdings total per filing and stops if neither fits.
12. **Stress is deliberately simple.** Two views: worst cumulative net outflow over a rolling window (default five
    reported days) against weekly liquid assets, and instantaneous redemption shocks (10-40% of net assets) against
    daily and weekly liquid assets. No price impact, no liquidity fees.
13. **Case studies cite files, not memory.** The `case` command writes every figure a written case study uses to
    CSVs under `outputs/<month>/case_<SERIESID>/`. Rating codes are labelled short-term or long-term by symbol
    pattern only; they are never mapped between agencies or summed across scales. Peer percentiles compare the fund
    with non-feeder funds of its own category at the same report date.
