# Case extract: JPMorgan Prime Money Market Fund (S000002969)
Report date 2026-08-31 · Category Prime · Source `20260810-20260908_nmfp.zip`

*Independent illustration from public SEC Form N-MFP data. Not a credit rating, and not the methodology of any rating agency. Every figure below is in a CSV in this folder.*

## Headline (memo and summary.csv)
- Net assets $92,079,337,441; WAM 42 days; WAL 67 days
- Lowest DLA 26.23% on 2026-08-31; lowest WLA 50.30% on 2026-08-05
- Month-end (2026-08-31): DLA 26.23%, WLA 51.48%; reported days 21; days below 50% WLA: 0; days below 25% DLA: 0  (`liquidity_daily.csv`)
- Worst rolling 5-day net flow $-3,171,973,780 ending 2026-08-31; net flow over the month $1,904,003,683  (`flows_daily.csv`)

## Peer position (`peer_stats.csv`)
Peers: non-feeder Prime funds at the same report date. Percentile = share of peers at or below the fund.

| Metric | Fund | Peers | P25 | Median | P75 | Fund percentile |
|---|---|---|---|---|---|---|
| wla_min_pct | 50.30 | 38 | 50.80 | 52.74 | 60.01 | 18 |
| dla_min_pct | 26.23 | 38 | 29.98 | 38.05 | 51.61 | 5 |
| wam_days | 42.00 | 38 | 24.00 | 38.00 | 42.75 | 74 |
| wal_days | 67.00 | 38 | 38.00 | 65.00 | 81.00 | 55 |
| top1_entity_pct | 3.44 | 38 | 3.39 | 4.25 | 4.82 | 29 |
| top5_entities_pct | 13.69 | 38 | 13.96 | 16.79 | 21.37 | 24 |
| repo_pct | 26.08 | 38 | 21.80 | 38.15 | 45.59 | 34 |
| other_collateral_repo_pct | 25.26 | 38 | 0.00 | 7.81 | 18.03 | 87 |
| rated_pct_of_assets | 98.10 | 25 | 96.40 | 97.68 | 99.80 | 60 |

## Largest credit entities (`top_entities.csv`)
1. BNP PARIBAS SA: 3.44%
2. SOCIETE GENERALE: 3.12%
3. CREDIT AGRICOLE CORPORATE AND INVESTMENT BANK (NON-TRAD REPO): 2.72%
4. TD SECURITIES (USA) LLC: 2.44%
5. WESTPAC BANKING CORPORATION: 1.97%
6. NATIXIS SECURITIES AMERICAS LLC: 1.93%
7. ING FINANCIAL MARKETS LLC DBA ING FINANCIAL MARKETS LLC: 1.89%
8. NATIONAL AUSTRALIA BANK LIMITED - LONDON BRANCH: 1.89%
9. SKANDINAVISKA ENSKILDA BANKEN AB (PUBL): 1.85%
10. ABN AMRO BANK N.V. DBA ABN AMRO BANK: 1.63%

## Repo (`repo_counterparties.csv`, `repo_collateral.csv`)
- 20 counterparties; top five:
  - SOCIETE GENERALE: 2.92% (other collateral 2.92%); collateral/position 1.059
  - BNP PARIBAS SA: 2.68% (other collateral 2.68%); collateral/position 1.078
  - TD SECURITIES (USA) LLC: 2.44% (other collateral 2.44%); collateral/position 1.063
  - CREDIT AGRICOLE CORPORATE AND INVESTMENT BANK (NON-TRAD REPO): 2.09% (other collateral 2.09%); collateral/position 1.059
  - NATIXIS SECURITIES AMERICAS LLC: 1.93% (other collateral 1.93%); collateral/position 1.071
- Collateral behind other repo: Corporate Debt Securities 51.2%; Asset-Backed Securities 13.9%; Equities 10.7%; Private Label Collateralized Mortgage Obligations 10.0%; Other Instrument 6.4%; U.S. Treasuries (including strips) 3.9%
- Collateral behind government repo: U.S. Treasuries (including strips) 100.0%

## Ratings as filed (`ratings_by_agency.csv`)
- Fitch, long-term/other: AA- 28.5%; AA+ 23.7%; AA 9.4%; A+ 8.5%
- Fitch, short-term: F1+ 67.2%; F1 13.8%
- Moody's, long-term/other: Aa1 28.3%; A1 24.1%; Aa3 13.8%; Aa2 12.6%
- Moody's, short-term: P-1 90.8%; VMIG1 0.6%
- S&P, long-term/other: A+ 41.4%; AA- 19.2%; A 12.4%; AA+ 10.8%
- S&P, short-term: A-1 64.4%; A-1+ 32.5%
