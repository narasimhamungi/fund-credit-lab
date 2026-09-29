# JPMorgan Prime Money Market Fund: prospectus and terms review

**Prepared by:** Narasimha Mungi, 30 September 2026 · **Companion to:** [rationale](rationale.md) (N-MFP data, 31 Aug 2026)

> Independent review of public documents. Not legal advice, not a credit rating, and not any rating agency's
> methodology.

## Sources

| Ref | Document |
|---|---|
| P | **Prospectus, J.P. Morgan Money Market Funds, Reserve Shares, 1 July 2026** ([PDF](https://www.rightprospectus.com/documents/JPMorgan/PR-MMR.pdf)). The cover lists JPMorgan Prime Money Market Fund as the family's only institutional fund. Reviewed: the fund summary, pp. 1–5 |
| FS | **Sponsor fact sheets**: [31 Oct 2025, Morgan](https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/literature/fact-sheet/money-market/FS-PMM-M.PDF), [31 Mar 2026, Premier](https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/literature/fact-sheet/money-market/FS-PMM-P.PDF), [30 Apr 2026, Capital](https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/literature/fact-sheet/money-market/FS-PMM-CAP.PDF), [31 Jul 2026, Agency](https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/literature/fact-sheet/money-market/FS-PMM-A.PDF). Liquidity and asset figures on them are fund-level |
| R | **Rule 2a-7** ([eCFR](https://www.ecfr.gov/current/title-17/chapter-II/part-270/section-270.2a-7)) and SEC Release 33-11211 (2023), which removed the redemption-gate provision |
| D | **This project's N-MFP outputs**, 31 Aug 2026 ([`outputs/2026-08/`](../../../outputs/2026-08/)) |

Fees and account minimums quoted below are for Reserve Shares. *Inference:* strategy, liquidity fees and
concentration are fund-level terms and apply to every share class.

## Terms summary

| Term | What the document says | Ref | August data (D) | Concern trigger |
|---|---|---|---|---|
| **NAV basis** | Floating NAV to four decimals, using market-based pricing | P p.1 | n/a | Market value falling materially below $1.0000 |
| **Maturity limits** | WAM 60 days or less; WAL 120 days or less; securities of 397 days or less | P p.1 | WAM 42, WAL 67 days | WAM trending toward 60 days |
| **Credit standard** | High-quality instruments judged to present minimal credit risk. **No minimum rating is stated.** Since the 2014 amendments, eligibility under the rule rests on the adviser's credit judgement, not ratings | P p.1; R | 98.1% of net assets rated at security level | Watch the rated share and grade mix month to month |
| **Industry concentration** | At least 25% of total assets in the banking industry under normal conditions; below 25% only as a temporary defensive measure | P pp.1–2 | At least 72.4% of net assets in financial-institution instruments (category-based) | Downgrades or funding stress among the largest bank entities |
| **Issuer diversification** | Not restated in the fund summary. The rule caps a taxable fund at 5% of total assets per issuer, excluding government securities, and aggregates affiliated issuers | R (d)(3)(i)(A) | Largest legal entity 3.44% | Any group approaching 5%. This project groups by LEI and so can understate affiliate groups the rule aggregates |
| **Mandatory liquidity fee** | Charged when daily net redemptions exceed **5% of net assets**. The fee is a good-faith estimate of the cost of selling a pro-rata slice of the portfolio, with a 1% default if that cost can't be estimated. Not charged if below 0.01% | P p.2 | Worst five-day net outflow 3.44% of net assets (cumulative). Single-day peak not computed here | Any fee event, or days near 5% while daily liquid assets sit near 25% |
| **Discretionary liquidity fee** | Up to **2%** of shares redeemed, if the adviser, as the Board's delegate, judges it in the fund's best interests | P p.2 | Not read by the tool yet | Any use: the adviser judged the fund under strain |
| **Redemption gates** | None described. The fund summary lists only fees, consistent with the 2023 removal of gates from the rule | P p.2; R | n/a | Stress must be absorbed by liquidity and fees |
| **Sponsor support** | The sponsor is not required to reimburse losses, and investors should not expect support at any time, including during market stress | P p.2 | n/a | None. Give the profile **no uplift** for the J.P. Morgan parent |
| **Repo** | A principal investment; counterparty default named as a risk. **No collateral-type limit is stated in the fund summary** | P pp.1, 4 | 25.3% of net assets against non-government collateral (87th percentile of peers); top-five cover 1.059–1.078x | More equity or private-label collateral, or a thinner cushion |
| **Portfolio flexibility** | May invest significantly in floating- and variable-rate securities, privately placed securities and when-issued trades. Privately placed securities are flagged as less liquid | P pp.1–2, 4–5 | The gap between WAM (42 days) and WAL (67 days) reflects floating-rate resets | A rising share of privately placed or longer-final-maturity paper |
| **Redemption access** | Any business day. Reserve Shares need $10,000,000 to open an account | P p.5 | n/a | Payment timing and suspension terms not yet reviewed (pp. 62–64) |

## Sponsor disclosures: the thin liquidity cushion is policy

The rationale rests on one month of filings. The sponsor's fact sheets extend that to ten months (FS; August from D):

| Month-end | Daily liquid assets | Weekly liquid assets | Fund assets |
|---|---|---|---|
| 31 Oct 2025 | 31.45% | 51.46% | $88.99bn |
| 31 Mar 2026 | 30.52% | 50.09% | $93.79bn |
| 30 Apr 2026 | 25.40% | 51.16% | $91.80bn |
| 31 Jul 2026 | 27.38% | 52.32% | $90.17bn |
| 31 Aug 2026 | 26.23% | 51.48% | $92.08bn |

- **Weekly liquidity** stayed between 50.1% and 52.3% at every month-end shown. The fund manages consistently to just
  above the 50% acquisition minimum.
- **Daily liquidity** ranged from 25.4% to 31.5%.
- **The August N-MFP figures sit inside the sponsor's range**, a further check on this project's parsing.
- **What it means for the rationale:** "liquidity on watch" describes a standing management choice. The signal to
  watch is a break in the pattern, not the level: a month-end below 50% weekly, or a fee event.

## What the terms change in the credit view

1. **No sponsor uplift.** The prospectus rules out relying on J.P. Morgan support. The "Strong" profile has to stand
   on the portfolio alone, and it does on credit quality and maturity.
2. **Fees replace gates.** With gates gone, a run is met with liquid assets first and fees second. That is why daily
   liquidity at the 5th percentile of prime peers matters more than the weekly position.
   - The mandatory fee is set by *net* redemptions, so one large redeemer can trigger it for everyone redeeming that
     day.
3. **The banking mandate is structural.** Bank concentration is stated policy (at least 25%), and August ran far
   above that floor. Monitor the credit of the largest bank entities (BNP Paribas, Société Générale, Crédit Agricole
   CIB), not the concentration level itself.
4. **Repo collateral is unconstrained by the fund summary.** The Statement of Additional Information may set limits;
   it has not been reviewed. Until then, monthly N-MFP data is the only outside view of what collateral the fund
   takes.

## Downgrade-style concerns

A sustained combination of these would weaken the profile:
- A mandatory-fee event, or any use of the discretionary fee.
- A month-end with weekly liquid assets below 50%. The fund came within 0.09pp of that level on 31 Mar 2026.
- Downgrades or funding stress among the largest bank entities.
- A shift in non-government repo collateral toward equities and private-label securities with no rise in
  overcollateralisation.

## Not covered

- Payment timing and suspension provisions ("Selling Fund Shares", pp. 62–64).
- The Statement of Additional Information: fundamental restrictions and diversification detail.
- Shareholder concentration: the beneficial owner table in the N-MFP data, not yet read by this project.
- Board oversight and the adviser's credit process.
