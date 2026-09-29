# Limitations

- **Not a credit rating.** This is an independent illustration built from public filings. It does not apply any rating
  agency's methodology, factors or scale, and nothing it produces should be read as an agency opinion.
- **Scope is US money market funds only.** Form N-MFP covers registered US money market funds. Bond funds,
  ETFs and closed-end funds are not covered.
- **Regulatory thresholds are not verified here.** The WAM (60 days) and WAL (120 days) limits are long-standing
  in Rule 2a-7. The daily (25%) and weekly (50%) liquid-asset minimums, and the tax-exempt treatment, reflect my understanding of
  the amended rule and must be checked against the current text before any flag is relied on.
- **As-filed data.** SEC states it cannot guarantee accuracy of the data sets; values are as filed by registrants.
- **Daily flow data** exists only where the filing form carries `DLYSHAREHOLDERFLOWREPORT`; where it is absent, the historical-flow stress is skipped.
- **Test status.** The unit tests run on synthetic fixtures built to the SEC layout. See the README for the status of live-data runs.
- **Stress is a screen, not a forecast.** It ignores market-price impact, redemption behaviour and liquidity fees.
