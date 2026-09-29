# JPMorgan Prime Money Market Fund: credit-profile illustration

**Data:** SEC Form N-MFP, report date 31 August 2026 (data set `20260810-20260908_nmfp.zip`) · **Series:** S000002969
**Prepared by:** Narasimha Mungi, 30 September 2026

> Independent illustration built from public filings with [fund-credit-lab](../../../README.md). **Not a credit
> rating**, not a Fitch product, and not the methodology of any rating agency. Assessments use this project's own
> scale (Strong / Adequate / Weak). Each figure is followed by a code in brackets for the file it comes from; the
> codes are listed at the end.

## Summary view

**Strong credit profile; liquidity is the monitoring point.**
- **Credit quality and diversification** are strong and granular.
- **Maturity** sits comfortably inside the Rule 2a-7 limits.
- **Liquidity** runs close to the SEC minimums. On the weekly measure that is normal for prime funds. On the daily
  measure the fund runs leaner than almost all its peers.
- **The distinctive exposure** is repo against non-government collateral: 25.3% of net assets, about three times the
  peer median. It is collateralised mainly by corporate debt, with about 6–8% overcollateralisation on the largest
  positions.

## Key profile drivers

**Credit quality: Strong.**
- 98.1% of net assets carries at least one security-level NRSRO rating, against a peer median of 97.7% [P].
- On each agency's short-term scale:
  - Moody's rates 90.8% of net assets P-1.
  - Fitch rates 67.2% F1+ and 13.8% F1.
  - S&P rates 32.5% A-1+ and 64.4% A-1 [R].
- Agencies cover different sets of securities, so these shares are not comparable across agencies and are not mapped
  to a common scale.

**Diversification: Strong at entity level; concentrated by sector.**
- The largest legal entity is BNP Paribas at 3.44% of net assets, and the top five total 13.69% [T]. Both sit below
  the prime peer median (4.25% and 16.79%) [P].
- By sector the book is concentrated, which is typical of prime funds. Financial company commercial paper, repo
  against non-government collateral, certificates of deposit and time deposits together make up at least 72.4% of net
  assets, and all of it is exposure to financial institutions [M].
- The figures are at legal-entity level. A banking group holding through several entities with different LEIs would
  be understated.

**Liquidity: Adequate, on watch.**
- *Weekly:* the lowest weekly liquid assets reading was 50.30% (5 Aug) and the month ended at 51.48% [L].
  - The fund sits at the 18th percentile of 38 prime funds.
  - The whole peer group runs close to the floor: half of the funds' lowest readings were at or below 52.74%, and a
    quarter at or below 50.80% [P].
  - The 50% rule is the binding constraint across the sector. This fund's weekly position is typical, not an outlier.
- *Daily:* daily liquid assets were lowest at month-end, 26.23% on 31 Aug. That is the 5th percentile of peers, whose
  median lowest reading was 38.05% [P].
- *Flows:* the worst five-day net outflow, $3.17bn or 3.4% of net assets, ended on the same day [F].
  - *Inference:* daily liquidity was drawn down to meet month-end redemptions, although the fund still took a net
    $1.90bn of inflows over the month [F].
  - No reported day fell below either SEC minimum [L].
  - Weekly liquid assets covered the worst five-day outflow 15.0 times [M].
- *Shocks:*
  - An instant redemption of 30% of net assets ($27.6bn) exceeds month-end daily liquid assets but is covered by
    weekly liquid assets [M].
- *Context:*
  - The SEC minimums (25% daily, 50% weekly) are acquisition tests. Below them a fund may only buy liquid assets,
    which is not a breach.
  - Published Fitch commentary for AAAmmf-rated funds cites liquidity of at least 10% daily and 30% weekly
    ([Fitch on CCLA funds, May 2026](https://www.ccla.co.uk/documents/fitch-reports-may-2026/download?inline=)). This
    figure is still to be confirmed against the current MMF Rating Criteria.
  - If it holds, the fund's thin headroom is a regulatory constraint on portfolio management rather than an
    agency-level liquidity weakness.

**Maturity and market risk: Strong.**
- WAM of 42 days leaves 18 days of headroom to the 60-day limit.
- WAL of 67 days leaves 53 days to the 120-day limit [M].
- WAM is longer than for most prime peers (74th percentile; median 38 days), so interest-rate reset risk is somewhat
  higher than the peer norm. WAL sits near the peer median [P].

**Repo and counterparties: the distinctive exposure.**
- Repo is 26.08% of net assets across 20 counterparties. Of that, 25.26% is against collateral other than Treasuries,
  agency securities and cash, the 87th percentile of peers (median 7.81%) [P].
- Collateral behind that repo, by value [C]:

  | Collateral type | Share |
  |---|---|
  | Corporate debt | 51.2% |
  | Asset-backed securities | 13.9% |
  | Equities | 10.7% |
  | Private-label CMOs | 10.0% |
  | Other instruments | 6.4% |
  | Treasuries | 3.9% |

- The five largest counterparties each hold 1.93–2.92% of net assets. Collateral value is 1.059–1.078 times the
  position [K], which is 5.9–7.8% overcollateralisation.
- *Inference:* the fund's first recourse is the dealer. The collateral is the second way out. Equities and
  private-label CMOs would be harder to liquidate at filed values in a stress than Treasuries, so the overcollateral
  margin is what absorbs the price move.

**Manager and structure: not assessed here.** N-MFP does not show governance, credit process or redemption terms. A
prospectus review (liquidity-fee terms and concentration limits) is the planned next step.

## Profile sensitivities

**What would weaken the profile:**
- Weekly liquid assets held below 50%, or falling toward the 25% board-notification level.
- Daily liquid assets below 25% for more than isolated days, or month-end outflows well above the 3.4% seen here.
- Repo against non-government collateral rising further, a shift toward equity or private-label collateral, or
  overcollateralisation falling below the current ~6–8%.
- Largest-entity exposure moving above the peer 75th percentile (4.82%), or WAM lengthening toward 60 days.

**What would strengthen it:** a larger daily liquidity buffer at month-ends, or less reliance on non-government repo.

## Data and limitations

- One month of as-filed data.
- Liquidity figures are each month's lowest daily readings, while stress uses month-end balances.
- Concentration is at legal-entity level.
- Repo is shown gross of collateral.
- Ratings are as filed and are not comparable across agencies.
- The peer group is the 38 non-feeder prime funds filing for 31 Aug 2026. It includes this fund, and percentiles are
  the share of peers at or below it.
- No Portfolio Credit Factor or other agency metric is computed.
- Full list: [limitations](../../limitations.md).

## Sources

All files are in [`outputs/2026-08/case_S000002969/`](../../../outputs/2026-08/case_S000002969/) unless noted.

| Code | File |
|---|---|
| M | fund memo, [`memos/S000002969_2026-08.md`](../../../outputs/2026-08/memos/S000002969_2026-08.md) |
| L | `liquidity_daily.csv` |
| F | `flows_daily.csv` |
| T | `top_entities.csv` |
| K | `repo_counterparties.csv` |
| C | `repo_collateral.csv` |
| R | `ratings_by_agency.csv` |
| P | `peer_stats.csv` |
