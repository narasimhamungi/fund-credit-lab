# Data dictionary

Source: SEC DERA *Form N-MFP Data Sets* (tab-delimited, one file per table). Field meanings
are from the SEC readme (`nmfp_readme.pdf`); only fields this project reads are listed.

## Live file layout

Checked on the `20260810-20260908_nmfp.zip` data set (N-MFP3 filings, report dates to 31 Aug 2026):

| Property | Live format | How the loader handles it |
|---|---|---|
| Member names | `NMFP_<TABLE>.tsv` (plus `NMFP_metadata.json`, `NMFP_readme.htm`) | `NMFP_` prefix stripped; bare names also accepted |
| Dates | `DD-MON-YYYY`, e.g. `31-AUG-2026` | parsed with that format; ISO 8601 accepted as fallback |
| Percentage fields | fractions of 1 (`0.4512` = 45.12%); median holdings total per filing was 1.0023 | converted to 0-100 after checking the scale (see below) |
| Encoding | UTF-8, per the readme | read as UTF-8 |

**Percentage scale check.** The loader sums `PERCENTAGEOFMONEYMARKETFUNDNET` per filing and takes the
median: about 1 means fractions (multiply by 100), about 100 means already percent; anything else stops
the run with an error. The same multiplier is applied to `PCTDAILYLIQUIDASSETS` and `PCTWEEKLYLIQUIDASSETS`.
Results are rounded to 6 decimals to remove float noise (source precision is 0.01pp).

**Unparsable values** (text in a numeric or date field) become missing and are listed in the
`_UNPARSED` table, which `validate.py` reports as `unparsed_value` findings.

## SUBMISSION
| Field | Meaning |
|---|---|
| `ACCESSION_NUMBER` | SEC-assigned unique id of the EDGAR submission (primary key) |
| `FILING_DATE` | Date filed. Used to pick the latest version when a report is amended |
| `SUBMISSIONTYPE` | `N-MFP3`, `N-MFP3/A` (amendment) or `NT N-MFP3` (notice of late filing, no data); older forms N-MFP, N-MFP1, N-MFP2 |
| `REPORTDATE` | Month-end date the report covers |
| `SERIESID` | EDGAR series identifier (`S` plus nine digits) |
| `NAMEOFSERIES` / `SERIES_NAME` | Series name as filed / as held by EDGAR |

## SERIESLEVELINFO
| Field | Meaning |
|---|---|
| `MONEYMARKETFUNDCATEGORY` | `Government`, `Prime`, `Single State` or `Other Tax Exempt` |
| `FEEDERFUNDFLAG` | `Y` if the series is a feeder fund (its portfolio is shares of a master fund) |
| `AVERAGEPORTFOLIOMATURITY` | Dollar-weighted average portfolio maturity, WAM (days) |
| `AVERAGELIFEMATURITY` | Dollar-weighted average life maturity, WAL (days) |
| `NETASSETOFSERIES` | Net assets of the series (USD) |

## SCHPORTFOLIOSECURITIES
| Field | Meaning |
|---|---|
| `SECURITY_ID` | Surrogate key for the security within the filing |
| `NAMEOFISSUER` | Issuer name (for repo, the counterparty) |
| `LEI` | Legal Entity Identifier of the issuer, where filed; used to group positions by legal entity |
| `INVESTMENTCATEGORY` | Category that most closely identifies the instrument (wording below) |
| `INVESTMENTMATURITYDATEWAM` | Maturity date used for WAM |
| `PERCENTAGEOFMONEYMARKETFUNDNET` | Position as a share of the fund's net assets (fraction in live files) |

`INVESTMENTCATEGORY` wording in the live data and the bucket `metrics.holding_bucket` assigns:

| Category (as filed) | Bucket |
|---|---|
| U.S. Treasury Debt | government |
| U.S. Government Agency Debt (if categorized as coupon-paying notes / no-coupon discount notes) | government |
| U.S. Treasury Repurchase Agreement, if collateralized only by U.S. Treasuries (including Strips) and cash | government_repo |
| U.S. Government Agency Repurchase Agreement, collateralized only by U.S. Government Agency securities, U.S. Treasuries, and cash | government_repo |
| Other Repurchase Agreement, if collateral falls outside Treasury, Government Agency and cash | other_repo |
| Every other category (commercial paper, CDs, time deposits, VRDNs, tender option bonds, municipal, ABCP, investment company, non-US sovereign, other) | credit |

## NRSRO
| Field | Meaning |
|---|---|
| `SECURITY_ID` | Links to SCHPORTFOLIOSECURITIES |
| `TYPE` | `SECURITY`, `DEMAND FEATURE`, `ENHANCEMENT` or `GUARANTOR` |
| `NAMEOFNRSRO` | Rating agency |
| `RATING` | Rating code as filed |

## LIQUIDASSETSDETAILS (one row per reported business day)
| Field | Meaning |
|---|---|
| `TOTLIQUIDASSETSNEARPCTDATE` | Date of the observation |
| `TOTVALUEDAILYLIQUIDASSETS`, `TOTVALUEWEEKLYLIQUIDASSETS` | Daily / weekly liquid assets (USD); weekly includes daily |
| `PCTDAILYLIQUIDASSETS`, `PCTWEEKLYLIQUIDASSETS` | The same as a share of total assets (fraction in live files) |

## DLYSHAREHOLDERFLOWREPORT (class level, one row per class per day)
| Field | Meaning |
|---|---|
| `CLASSESID` | Share class id |
| `DAILYGROSSSUBSCRIPTIONS`, `DAILYGROSSREDEMPTIONS` | Gross subscriptions and redemptions (USD) |
| `DAILYSHAREHOLDERFLOWDATE` | Date |

## COLLATERALISSUERS (read only by the `case` command, filtered to one filing)
| Field | Meaning |
|---|---|
| `SECURITY_ID` | Links to the repo position in SCHPORTFOLIOSECURITIES |
| `NAMEOFCOLLATERALISSUER` | Issuer of the collateral |
| `VALUEOFCOLLATERALTOTHENEARESTC` | Value of the collateral (USD) |
| `CTGRYINVESTMENTSRPRSNTSCOLLATE` | Category that most closely represents the collateral |

`INCLUDINGVALUEOFANYSPONSORSUPP` (SCHPORTFOLIOSECURITIES) gives the repo position value in USD; collateral value
divided by it is the collateral cover shown per counterparty.
