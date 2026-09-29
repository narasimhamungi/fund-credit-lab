# Live-data validation

Run: `fund-credit-lab analyze` on the SEC data set `20260810-20260908_nmfp.zip`, report date 31 Aug 2026.
Result: 295 series analysed, 32 feeder funds left out, 2 data-quality findings
(one `holdings_total`, one `matured_holding`). Percentages were filed as fractions and converted.

## Tie-out against sponsor disclosures

Two of the largest funds, checked against figures the sponsors publish themselves (checked 29 Sep 2026).

### Vanguard Federal Money Market Fund (S000004462), same date

| Measure | This tool (N-MFP, 31 Aug 2026) | Vanguard fund page (as of 31 Aug 2026) | Result |
|---|---|---|---|
| Net assets | $375,003,028,961 | $376.0B | Within 0.3%. The sponsor does not state its definition; the gap is not explained. |
| WAL | 52 days | 52.0 days | Match |

### Schwab Prime Advantage Money Fund (S000004508), different date

Schwab's product pages show only current figures (as of 28 Sep 2026), so this is a consistency check, not a tie-out.
Series net assets are the sum of the share classes.

| Measure | This tool (31 Aug 2026) | Schwab product pages (28 Sep 2026) | Result |
|---|---|---|---|
| Net assets | $393,048,323,934 | $392,448,761,794 (Investor $249,094,931,260 + Ultra $143,353,830,534) | Consistent (-0.15% four weeks later) |
| WAM / WAL | 37 / 56 days | 31.65 / 55.74 days | Consistent |
| Daily / weekly liquid assets | month low 37.91% / 54.93% | 38.53% / 55.09% | Consistent in level and scale |

## Parser cross-check (same source, not independent data)

sevendayyield.com publishes figures derived from the same N-MFP filings. For Vanguard Federal at August 2026
month-end it shows WAM 24 days, WAL 52 days, daily liquid assets 52.5% and weekly 68.3%. This tool reads WAM 24 and
WAL 52; its liquidity figures are the month's lowest readings (48.64% and 67.42%), which sit below the month-end
values as they should. This checks the parsing, not the underlying data.

## Not validated

Issuer concentration, repo counterparties and rating coverage have not been reconciled to a sponsor's holdings
file. The next check is to tie one fund's top five issuers to its published monthly holdings.
