# Limitations

- **Not a credit rating.** This is an independent illustration built from public filings. It does not apply any rating
  agency's methodology, factors or scale, and nothing it produces should be read as an agency opinion.
- **Scope is US money market funds only.** Form N-MFP covers registered US money market funds. Bond funds,
  ETFs and closed-end funds are not covered.
- **Flags are screens, not compliance findings.** The daily and weekly minimums are acquisition tests: a fund below
  them may only buy liquid assets, which is not itself a breach. Liquidity is measured as the lowest reported daily
  value in the month.
- **Concentration is at legal-entity level.** Positions are grouped by LEI, or by issuer name where no LEI is filed.
  Entities in the same group (for example a bank and its branches or affiliates with different LEIs) are not combined,
  so group exposure can be understated.
- **Repo is shown gross of collateral.** Counterparty exposure is the repo position itself; the collateral table
  (`COLLATERALISSUERS`) is not read, so there is no look-through to collateral quality.
- **Feeder funds are left out by default** (see decisions). Their master funds are analysed only if they file their own N-MFP.
- **Rating coverage counts securities, not exposure.** A small unrated position counts the same as a large one.
- **One month at a time.** Each run analyses one report date; there is no trend across months yet.
- **As-filed data.** SEC states it cannot guarantee accuracy of the data sets; values are as filed by registrants.
- **Daily flow data** exists only where the filing carries `DLYSHAREHOLDERFLOWREPORT`; where it is absent, the
  historical-flow stress is skipped.
- **Stress is a screen, not a forecast.** It ignores market-price impact, redemption behaviour and liquidity fees.
- **Test status.** Unit tests run on synthetic fixtures written in the live SEC layout. See the README for the status
  of live-data runs.

## Regulatory values and sources

Checked 29 Sep 2026.

| Value | Rule | Source |
|---|---|---|
| WAM at most 60 days; WAL at most 120 days | Rule 2a-7(d)(1)(ii)-(iii) | SEC staff Q&A on the 2010 amendments (sec.gov/files/mmfreform-imqa.htm). The 2023 amendments specified how WAM and WAL are calculated; they did not change the limits (Release 33-11211). |
| Daily liquid assets at least 25% of total assets, as an acquisition test; does not apply to tax-exempt funds | Rule 2a-7(d)(4)(ii) | Current rule text, eCFR 17 CFR 270.2a-7 |
| Weekly liquid assets at least 50% of total assets, as an acquisition test; all funds | Rule 2a-7(d)(4)(iii) | Current rule text, eCFR 17 CFR 270.2a-7 |
| Board notified within one business day if daily liquid assets fall below 12.5% or weekly below 25% | Rule 2a-7, as amended by Release 33-11211 | eCFR 17 CFR 270.2a-7; SEC Release 33-11211 (2023) |
| Tax-exempt fund: holds itself out as distributing income exempt from regular federal income tax | Rule 2a-7(a)(23) | eCFR 17 CFR 270.2a-7 |
